# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test cases for Product model.

Run tests with:
    nosetests
    coverage report -m

To debug only this test module:
    nosetests --stop tests/test_models.py:TestProductModel
"""

import os
import logging
import unittest
from decimal import Decimal

from service import app
from service.models import Category, DataValidationError, Product, db
from tests.factories import ProductFactory


DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

##############################################################################
# product model test cases
##############################################################################
# pylint: disable=too-many-public-methods


class TestProductModel(unittest.TestCase):
    """Test cases for the Product model."""
    @classmethod
    def setUpClass(cls):
        """Configure and initialize the app once before all tests."""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Close the database session after all tests complete."""
        db.session.close()

    def setUp(self):
        """Run before each test: clear Product rows and commit."""
        db.session.query(Product).delete()
        db.session.commit()

    def tearDown(self):
        """Run after each test: remove the current session."""
        db.session.remove()

    ######################################################################
    # test cases
    ######################################################################

    def test_create_a_product(self):
        """Create a product instance and verify its attributes."""
        product = Product(
            name="Fedora",
            description="A red hat",
            price=12.50,
            available=True,
            category=Category.CLOTHS,
        )
        self.assertEqual(str(product), "<Product Fedora id=[None]>")
        self.assertTrue(product is not None)
        self.assertEqual(product.id, None)
        self.assertEqual(product.name, "Fedora")
        self.assertEqual(product.description, "A red hat")
        self.assertEqual(product.available, True)
        self.assertEqual(product.price, 12.50)
        self.assertEqual(product.category, Category.CLOTHS)

    def test_add_a_product(self):
        """Create a product and persist it to the database."""
        products = Product.all()
        self.assertEqual(products, [])
        product = ProductFactory()
        product.id = None
        product.create()
        # verify an id was assigned and the product is in the DB
        self.assertIsNotNone(product.id)
        products = Product.all()
        self.assertEqual(len(products), 1)
        new_product = products[0]
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(Decimal(new_product.price), product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)

    # add additional test cases below
    def test_read_a_product(self):
        """Persist a product then read it back by id."""
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        found_product = Product.find(product.id)
        self.assertEqual(found_product.name, product.name)
        self.assertEqual(found_product.description, product.description)
        self.assertEqual(found_product.price, product.price)
        self.assertEqual(found_product.available, product.available)
        self.assertEqual(found_product.category, product.category)

    def test_update_a_product(self):
        """Update fields on a product and verify persistence."""
        product = ProductFactory()
        product.id = None
        product.create()
        # confirm the product was created with the expected string repr
        self.assertEqual(str(product), f"<Product {product.name} id=[{product.id}]>")
        self.assertTrue(product is not None)
        self.assertIsNotNone(product.id)
        # change description and update
        new_description = "Full of Fibers and Vitamin A"
        product.description = new_description
        original_id = product.id
        product.update()
        # id should remain the same and description should be updated
        self.assertEqual(product.id, original_id)
        self.assertEqual(product.description, new_description)
        products = Product.all()
        self.assertEqual(len(products), 1)
        updated_product = products[0]
        self.assertEqual(updated_product.id, original_id)
        self.assertEqual(updated_product.name, product.name)
        self.assertEqual(updated_product.description, new_description)

    def test_update_product_without_id_raises_error(self):
        """Updating a product without an id should raise a DataValidationError."""
        product = ProductFactory()
        product.id = None
        product.description = "What is love?"
        self.assertRaises(DataValidationError, product.update)

    def test_delete_a_product(self):
        """Delete a product and verify it is removed from the DB."""
        product = ProductFactory()
        product.create()
        self.assertEqual(len(Product.all()), 1)
        product.delete()
        self.assertEqual(len(Product.all()), 0)

    def test_list_all_produsct(self):
        """Create several products and list them all."""
        self.assertEqual(len(Product.all()), 0)
        for _ in range(5):
            product = ProductFactory()
            product.create()
        products = Product.all()
        self.assertEqual(len(products), 5)

    def test_find_a_product_by_name(self):
        """Find products by name and verify results."""
        for _ in range(5):
            product = ProductFactory()
            product.create()
        products = Product.all()
        name = products[0].name
        count = 0
        for product in products:
            if product.name == name:
                count += 1
        found = Product.find_by_name(name)
        self.assertEqual(found.count(), count)
        for product in found:
            self.assertEqual(product.name, name)

    def test_find_a_product_availability(self):
        """Query products by availability and check returned set."""
        for _ in range(10):
            product = ProductFactory()
            product.create()
        products = Product.all()
        available = products[0].available
        count = len([product for product in products if product.available == available])
        found = Product.find_by_availability(available)
        self.assertEqual(found.count(), count)
        for product in found:
            self.assertEqual(product.available, available)

    def test_find_a_product_category(self):
        """Query products by category and verify matching items."""
        for _ in range(10):
            product = ProductFactory()
            product.create()
        products = Product.all()
        category = products[0].category
        count = len([product for product in products if product.category == category])
        found = Product.find_by_category(category)
        self.assertEqual(found.count(), count)
        for product in found:
            self.assertEqual(product.category, category)

    def test_serialize(self):
        """Serialize a product to a dictionary and check fields."""
        product = ProductFactory()
        result = product.serialize()
        self.assertEqual(product.name, result["name"])
        self.assertEqual(product.description, result["description"])
        self.assertEqual(product.price, Decimal(result["price"]))
        self.assertEqual(product.available, result["available"])
        self.assertEqual(product.category.name, result["category"])

    def test_deserialize(self):
        """Deserialize a dictionary into a Product instance."""
        data = ProductFactory().serialize()
        product = Product()
        product.deserialize(data)
        self.assertEqual(product.name, data["name"])
        self.assertEqual(product.description, data["description"])
        self.assertEqual(product.price, Decimal(data["price"]))
        self.assertEqual(product.available, data["available"])
        self.assertEqual(product.category.name, data["category"])

    def test_deserialize_without_available_raises_error(self):
        """Invalid deserialize input should raise DataValidationError."""
        data = ProductFactory().serialize()
        data["available"] = "Not A Bool"
        product = Product()
        self.assertRaises(DataValidationError, product.deserialize, data)
        bad_data = None
        self.assertRaises(DataValidationError, product.deserialize, bad_data)

    def test_find_by_price(self):
        """Find products by price and ensure returned set matches expected."""
        for _ in range(10):
            product = ProductFactory()
            product.create()
        products = Product.all()
        price = products[0].price
        count = len([product for product in products if product.price == price])
        found = Product.find_by_price(price)
        self.assertEqual(found.count(), count)
        for product in found:
            self.assertEqual(product.price, price)

    def test_find_by_price_decimal_conversion(self):
        """Ensure find_by_price converts string input to Decimal correctly."""
        product = ProductFactory()
        product.price = "3.14"
        product.create()
        found = Product.find_by_price("3.14")
        self.assertEqual(found[0].price, Decimal("3.14"))
