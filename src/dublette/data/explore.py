import click

from splink.exploratory import completeness_chart, profile_columns
from splink import DuckDBAPI


def missing_data(df):
    db_api = DuckDBAPI()
    click.echo("📊 Missing Values")
    chart = completeness_chart(df, db_api=db_api)
    chart.save("output/completeness_chart.png", format="png")


def column_profile(df):
    click.echo("📊 Column Profiles")
    chart = profile_columns(df, db_api=DuckDBAPI())
    chart.save("output/column_profiles_chart.png", format="png")
