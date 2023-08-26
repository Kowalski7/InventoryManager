from datetime import date
from dateutil.relativedelta import relativedelta
from io import BytesIO
from flask import Blueprint, jsonify, make_response
from sqlalchemy import and_, func
import plotly.graph_objects as go
import textwrap
from plotly.subplots import make_subplots
from PIL import Image

from app.middleware.tokenValidator import token_required
from app.models.PurchasedProducts import PurchasedProducts
from app.models.Transactions import Transactions
from app.models.ArchivedInventory import ArchivedInventory
from app.utils import query_product_by_barcode


statistics = Blueprint('statistics', __name__,
                       url_prefix='/api/statistics')


@statistics.route('/<barcode>/sales-distribution')
@token_required
def product_sales_distribution(user, barcode):
    if not user or not set(user.roles).intersection(['ROLE_EMPLOYEE', 'ROLE_DEVELOPER']):
        return make_response(jsonify({"message": "Forbidden"}), 403)

    # ? Search for the product by barcode
    inventory_lookup, _ = query_product_by_barcode(barcode)
    if not inventory_lookup:
        return make_response(jsonify({"message": "Product not found!"}), 404)

    # ? Query all sales of the product
    sales = PurchasedProducts.query.with_entities(PurchasedProducts, Transactions).filter(PurchasedProducts.product_name == inventory_lookup[0][0].product_name).outerjoin(
        Transactions, (PurchasedProducts.transaction_id == Transactions.id)).all()

    distr = {
        "sold_base_price": 0,
        "sold_discount": 0,
        "sold_profit": 0,
        "disposed": 0
    }
    for sale in sales:
        if sale[0].payed_price / sale[0].item_count == inventory_lookup[0][0].base_price:
            distr["sold_base_price"] += sale[0].item_count
        elif sale[0].payed_price / sale[0].item_count < inventory_lookup[0][0].base_price:
            distr["sold_discount"] += sale[0].item_count
        else:
            distr["sold_profit"] += sale[0].item_count

    # ? Query all disposals of the product
    disposals = ArchivedInventory.query.filter(
        ArchivedInventory.product_barcode == inventory_lookup[0][0].product_barcode).all()

    distr["disposed"] = sum(disposal.product_remain for disposal in disposals)
    split_title = textwrap.wrap(inventory_lookup[0][0].product_name, width=50)

    # ? Create the pie chart
    fig = make_subplots(rows=2, cols=1, specs=[[{'type': 'domain'}], [
                        {}]], row_heights=[0.75, 0.25])
    if len(sales) > 0:
        fig.add_trace(go.Pie(labels=['Sold at base price', 'Sold at discount', 'Sold at profit', 'Disposed'], values=[
                    distr['sold_base_price'], distr['sold_discount'], distr['sold_profit'], distr['disposed']]), row=1, col=1)
    else:
        fig.add_annotation(text="Not enough data to generate a chart", font_size=45, xref="paper", yref="paper", x=0.5, y=0.75, showarrow=False)
    fig.add_annotation(
        text="<br>".join(split_title), font_size=32, xref="paper", yref="paper", x=0.5, y=0.25, showarrow=False)

    fig.update_layout(
        title={
            'text': "Sales distribution",
            'y': 0.98,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        legend={
            "yanchor": "bottom",
            "y": 0,
            "xanchor": "center",
            "x": 0.5
        },
        font={
            "size": 32
        }
    )

    img_bytes = fig.to_image(format="jpg", width=1000, height=1500)
    return make_response(img_bytes, 200, {'Content-Type': 'image/jpeg'})


@statistics.route('/<barcode>/monthly-sales')
@token_required
def product_monthly_sales(user, barcode):
    if not user or not set(user.roles).intersection(['ROLE_EMPLOYEE', 'ROLE_DEVELOPER']):
        return make_response(jsonify({"message": "Forbidden"}), 403)

    # ? Search for the product by barcode
    inventory_lookup, _ = query_product_by_barcode(barcode)
    if not inventory_lookup:
        return make_response(jsonify({"message": "Product not found!"}), 404)

    # ? Query all sales of the product
    # sales = PurchasedProducts.query.with_entities(func.date_format(Transactions.date, "%Y-%m"), func.sum(PurchasedProducts.item_count)).filter(PurchasedProducts.product_name == inventory_lookup[0][0].product_name).outerjoin(
    #     Transactions, (PurchasedProducts.transaction_id == Transactions.id)).group_by(func.date_format(Transactions.date, "%Y-%m")).order_by(func.date_format(Transactions.date, "%Y-%m")).all()

    current_date = (date.today() - relativedelta(years=1)).replace(day=1)

    report = {}

    while current_date < date.today():
        sales = PurchasedProducts.query.with_entities(func.date_format(Transactions.date, "%Y-%m-%d"), func.sum(PurchasedProducts.item_count)).filter(and_(PurchasedProducts.product_name == inventory_lookup[0][0].product_name, Transactions.date.between(current_date, current_date + relativedelta(months=1)))).outerjoin(
        Transactions, (PurchasedProducts.transaction_id == Transactions.id)).group_by(func.date_format(Transactions.date, "%Y-%m-%d")).order_by(func.date_format(Transactions.date, "%Y-%m-%d")).all()

        report[current_date.strftime("%Y-%m")] = sum(sale[1] for sale in sales)

        current_date += relativedelta(months=1)

    # ? Create the line chart
    fig=go.Figure([go.Scatter(x=list(report.keys()), y=list(report.values()))])

    # fig = px.line(data, x='date', y='qty')

    fig.update_layout(
        title=f"Monthly sales – {inventory_lookup[0][0].product_name}",
        legend=dict(
            yanchor="bottom",
            y=0,
            xanchor="center",
            x=0.5
        ),
        font=dict(
            size=30
        ),
    )

    img_bytes=fig.to_image(format="jpg", width=1500, height=1000)

    img_rotated = Image.open(BytesIO(img_bytes)).transpose(Image.ROTATE_270)
    img = BytesIO()
    img_rotated.save(img, format="JPEG", quality=100)
    return make_response(img.getvalue(), 200, {'Content-Type': 'image/jpeg'})


@statistics.route('/<barcode>/daily-sales')
@token_required
def product_daily_sales(user, barcode):
    if not user or not set(user.roles).intersection(['ROLE_EMPLOYEE', 'ROLE_DEVELOPER']):
        return make_response(jsonify({"message": "Forbidden"}), 403)

    # ? Search for the product by barcode
    inventory_lookup, _ = query_product_by_barcode(barcode)
    if not inventory_lookup:
        return make_response(jsonify({"message": "Product not found!"}), 404)

    # ? Query all sales of the product
    # sales = PurchasedProducts.query.with_entities(func.date_format(Transactions.date, "%m-%d"), func.sum(PurchasedProducts.item_count)).filter(PurchasedProducts.product_name == inventory_lookup[0][0].product_name).outerjoin(
    #     Transactions, (PurchasedProducts.transaction_id == Transactions.id)).group_by(func.date_format(Transactions.date, "%Y-%m-%d")).order_by(func.date_format(Transactions.date, "%Y-%m-%d").desc()).limit(31).all()

    current_date = (date.today() - relativedelta(months=1))
    report = {}

    while current_date < date.today():
        sales = PurchasedProducts.query.with_entities(func.date_format(Transactions.date, "%Y-%m-%d"), PurchasedProducts.item_count).filter(and_(PurchasedProducts.product_name == inventory_lookup[0][0].product_name, func.date_format(Transactions.date, "%Y-%m-%d") == current_date)).outerjoin(
        Transactions, (PurchasedProducts.transaction_id == Transactions.id)).order_by(func.date_format(Transactions.date, "%Y-%m-%d")).all()

        report[current_date.strftime("%Y-%m-%d")] = sum(sale[1] for sale in sales)

        current_date += relativedelta(days=1)

    # return make_response(jsonify(report))

    # ? Create the line chart
    fig=go.Figure([go.Scatter(x=list(report.keys()), y=list(report.values()))])

    # fig = px.line(data, x='date', y='qty')

    fig.update_layout(
        title=f"Daily sales – {inventory_lookup[0][0].product_name}",
        legend=dict(
            yanchor="bottom",
            y=0,
            xanchor="center",
            x=0.5
        ),
        font=dict(
            size=30
        ),
    )

    img_bytes=fig.to_image(format="jpg", width=1500, height=1000)

    img_rotated = Image.open(BytesIO(img_bytes)).transpose(Image.ROTATE_270)
    img = BytesIO()
    img_rotated.save(img, format="JPEG", quality=100)
    return make_response(img.getvalue(), 200, {'Content-Type': 'image/jpeg'})
