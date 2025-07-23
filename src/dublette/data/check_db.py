import duckdb
import click

DEFAULT_DB_PATH = "output/splink_data.duckdb"

def list_tables(db_path=DEFAULT_DB_PATH):
    con = duckdb.connect(db_path)
    tables = con.execute("SHOW TABLES").fetchall()
    con.close()
    return [t[0] for t in tables]

def list_columns(table_name, db_path=DEFAULT_DB_PATH):
    con = duckdb.connect(db_path)
    cols = con.execute(f"PRAGMA table_info('{table_name}')").fetchall()
    con.close()
    return [c[1] for c in cols]

def drop_table(table_name, db_path=DEFAULT_DB_PATH):
    con = duckdb.connect(db_path)
    con.execute(f"DROP TABLE IF EXISTS {table_name}")
    con.close()
    click.echo(f"Tabelle '{table_name}' wurde gelöscht.")

@click.group()
@click.option('--db-path', default=DEFAULT_DB_PATH, show_default=True, help='Pfad zur DuckDB-Datenbank')
@click.pass_context
def cli(ctx, db_path):
    ctx.ensure_object(dict)
    ctx.obj['db_path'] = db_path

@cli.command()
@click.pass_context
def list(ctx):
    tables = list_tables(ctx.obj['db_path'])
    click.echo("Tabellen in der Datenbank:")
    for t in tables:
        click.echo(f"- {t}")

@cli.command()
@click.argument('table_name')
@click.pass_context
def columns(ctx, table_name):
    cols = list_columns(table_name, ctx.obj['db_path'])
    click.echo(f"Spalten in '{table_name}':")
    for c in cols:
        click.echo(f"- {c}")

@cli.command()
@click.argument('table_name')
@click.pass_context
def drop(ctx, table_name):
    drop_table(table_name, ctx.obj['db_path'])

if __name__ == "__main__":
    cli(obj={})
