from typing import TYPE_CHECKING

from alembic import autogenerate
from alembic.autogenerate import api
from alembic.operations import ops
if TYPE_CHECKING:
    from sqlalchemy import Connection

from alembic_postgresql_enum import CreateEnumOp, DropEnumOp
from tests.schemas import get_schema_without_enum, get_schema_with_enum_variants, USER_STATUS_ENUM_NAME, DEFAULT_SCHEMA, \
    USER_TABLE_NAME, USER_STATUS_COLUMN_NAME
from tests.utils.migration_context import create_migration_context


def test_create_enum_render(connection: 'Connection'):
    """Check that library correctly creates enum before its use inside add_column"""
    database_schema = get_schema_without_enum()
    database_schema.create_all(connection)

    new_enum_variants = ["active", "passive"]

    target_schema = get_schema_with_enum_variants(new_enum_variants)

    context = create_migration_context(connection, target_schema)

    template_args = {}
    autogenerate._render_migration_diffs(context, template_args)

    # assert 0
    assert (template_args["upgrades"] ==
            f"""# ### commands auto generated by Alembic - please adjust! ###
    sa.Enum({', '.join(map(repr, new_enum_variants))}, name='{USER_STATUS_ENUM_NAME}').create(op.get_bind())
    op.add_column('{USER_TABLE_NAME}', sa.Column('{USER_STATUS_COLUMN_NAME}', postgresql.ENUM({', '.join(map(repr, new_enum_variants))}, name='{USER_STATUS_ENUM_NAME}'), nullable=True))
    # ### end Alembic commands ###""")
    assert (template_args["downgrades"] ==
            f"""# ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('{USER_TABLE_NAME}', '{USER_STATUS_COLUMN_NAME}')
    sa.Enum({', '.join(map(repr, new_enum_variants))}, name='{USER_STATUS_ENUM_NAME}').drop(op.get_bind())
    # ### end Alembic commands ###""")


def test_create_enum_diff_tuple(connection: 'Connection'):
    """Check that library correctly creates enum before its use inside add_column"""
    database_schema = get_schema_without_enum()
    database_schema.create_all(connection)

    new_enum_variants = ["active", "passive"]

    target_schema = get_schema_with_enum_variants(new_enum_variants)

    context = create_migration_context(connection, target_schema)

    autogen_context = api.AutogenContext(context, target_schema)

    uo = ops.UpgradeOps(ops=[])
    autogenerate._produce_net_changes(autogen_context, uo)

    diffs = uo.as_diffs()
    assert len(diffs) == 2
    create_enum_tuple, add_column_tuple = diffs

    assert create_enum_tuple == (
        CreateEnumOp.operation_name,
        USER_STATUS_ENUM_NAME,
        DEFAULT_SCHEMA,
        tuple(new_enum_variants)
    )
    assert add_column_tuple[0] == 'add_column'


def test_delete_enum_render(connection: 'Connection'):
    """Check that library correctly removes unused enum"""
    old_enum_variants = ["active", "passive"]
    database_schema = get_schema_with_enum_variants(old_enum_variants)
    database_schema.create_all(connection)

    target_schema = get_schema_without_enum()

    context = create_migration_context(connection, target_schema)

    template_args = {}
    autogenerate._render_migration_diffs(context, template_args)

    assert (template_args["upgrades"] ==
            f"""# ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('{USER_TABLE_NAME}', '{USER_STATUS_COLUMN_NAME}')
    sa.Enum({', '.join(map(repr, old_enum_variants))}, name='{USER_STATUS_ENUM_NAME}').drop(op.get_bind())
    # ### end Alembic commands ###""")
    # For some reason alembic decided to add redundant autoincrement=False on downgrade
    assert (template_args["downgrades"] ==
            f"""# ### commands auto generated by Alembic - please adjust! ###
    sa.Enum({', '.join(map(repr, old_enum_variants))}, name='{USER_STATUS_ENUM_NAME}').create(op.get_bind())
    op.add_column('{USER_TABLE_NAME}', sa.Column('{USER_STATUS_COLUMN_NAME}', postgresql.ENUM({', '.join(map(repr, old_enum_variants))}, name='{USER_STATUS_ENUM_NAME}'), autoincrement=False, nullable=True))
    # ### end Alembic commands ###""")


def test_delete_enum_diff_tuple(connection: 'Connection'):
    """Check that library correctly removes unused enum"""
    old_enum_variants = ["active", "passive"]
    database_schema = get_schema_with_enum_variants(old_enum_variants)
    database_schema.create_all(connection)

    target_schema = get_schema_without_enum()

    context = create_migration_context(connection, target_schema)

    autogen_context = api.AutogenContext(context, target_schema)

    uo = ops.UpgradeOps(ops=[])
    autogenerate._produce_net_changes(autogen_context, uo)

    diffs = uo.as_diffs()
    assert len(diffs) == 2
    remove_column_tuple, create_enum_tuple = diffs

    assert remove_column_tuple[0] == 'remove_column'
    assert create_enum_tuple == (
        DropEnumOp.operation_name,
        USER_STATUS_ENUM_NAME,
        DEFAULT_SCHEMA,
        tuple(old_enum_variants)
    )
