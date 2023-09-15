import operator
import os

from flask import Blueprint, current_app, render_template

from application.data.dao import ApplicationDao

HTML_BLUEPRINT = Blueprint("routes_html", __name__)

PRODUCT_IMAGE_URL_PREFIX = os.environ.get("PRODUCT_IMAGE_URL_PREFIX")


@HTML_BLUEPRINT.route("/")
def homepage():
    dao = _get_dao()

    categories = dao.get_categories()
    categories.sort(key=operator.attrgetter("display_name"))

    return render_template("index.html", categories=categories)


@HTML_BLUEPRINT.route("/price_history/<product_id>")
def price_history_page(product_id: int):
    product_id = int(product_id)

    dao = _get_dao()
    price_history = dao.get_product_price_history(product_id)
    product_display_name = dao.get_product_display_name(product_id)

    if PRODUCT_IMAGE_URL_PREFIX:
        padded_product_id = str(product_id).zfill(9)
        product_image_url = f"{PRODUCT_IMAGE_URL_PREFIX.rstrip('/')}/{padded_product_id}.jpg"
    else:
        product_image_url = None

    return render_template(
        "price_history.html",
        product_id=product_id,
        dates=price_history.dates,
        prices=price_history.prices,
        minimum_price=price_history.minimum_price,
        maximum_price=price_history.maximum_price,
        product_image_url=product_image_url,
        product_display_name=product_display_name,
    )


@HTML_BLUEPRINT.route("/products/<search_query>")
def products_page(search_query: str):
    dao = _get_dao()
    products = dao.get_products(search_query)
    products.sort(key=operator.attrgetter("display_name"))
    num_results = len(products)

    return render_template("products.html", search_query=search_query, products=products, num_results=num_results)


@HTML_BLUEPRINT.route("/category/<category_id>")
def category_page(category_id: int):
    category_id = int(category_id)
    dao = _get_dao()

    display_name = dao.get_category_display_name(category_id)
    products = dao.get_category_products(category_id)
    products.sort(key=operator.attrgetter("display_name"))
    num_products = len(products)

    return render_template("category.html", display_name=display_name, products=products, num_products=num_products)


def _get_dao() -> ApplicationDao:
    return current_app.config["DB"]
