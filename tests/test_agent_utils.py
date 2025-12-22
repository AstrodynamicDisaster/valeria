import decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from core.agent.payroll_lines import build_payroll_lines
from core.agent.state import ProcessingState
from core.agent.utils import (
    extract_period_dates,
    format_periodo,
    parse_date,
    parse_spanish_name,
    period_reference_date,
)
from core.models import Base, PayrollLine


def test_parse_spanish_name_with_separator():
    first, last, last2 = parse_spanish_name("GARCIA LOPEZ --- JUAN CARLOS")
    assert first == "JUAN CARLOS"
    assert last == "GARCIA"
    assert last2 is None


def test_parse_spanish_name_without_separator():
    first, last, last2 = parse_spanish_name("GARCIA LOPEZ MARTINEZ JUAN")
    assert first == "JUAN"
    assert last == "GARCIA"
    assert last2 == "LOPEZ"


def test_parse_date_formats():
    assert parse_date("2024-03-15").isoformat() == "2024-03-15"
    assert parse_date("15-03-2024").isoformat() == "2024-03-15"
    assert parse_date("15/03/2024").isoformat() == "2024-03-15"
    assert parse_date("") is None


def test_period_helpers():
    periodo = {"desde": "2024-03-01", "hasta": "2024-03-31"}
    start, end = extract_period_dates(periodo)
    assert start.isoformat() == "2024-03-01"
    assert end.isoformat() == "2024-03-31"
    assert period_reference_date(periodo).isoformat() == "2024-03-31"
    assert format_periodo(periodo) == "2024-03-01 → 2024-03-31"


def test_build_payroll_lines_creates_records(tmp_path):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        created = build_payroll_lines(
            session,
            payroll_id=1,
            collections=[
                ("devengo", [{"concepto": "SALARIO BASE", "importe": "1000.25"}]),
                ("deduccion", [{"concepto": "IRPF", "importe": "150.10"}]),
            ],
        )
        session.commit()

        assert len(created) == 2
        stored = session.query(PayrollLine).order_by(PayrollLine.category).all()
        assert stored[0].category == "deduccion"
        assert stored[0].importe == decimal.Decimal("150.10")
        assert stored[1].category == "devengo"
        assert stored[1].importe == decimal.Decimal("1000.25")


def test_processing_state_dataclass():
    state = ProcessingState(client_id="abc")
    state.employees_created = 5
    as_dict = state.to_dict()

    assert as_dict["client_id"] == "abc"
    state.reset()
    assert state.client_id == "abc"
    assert state.employees_created == 0
