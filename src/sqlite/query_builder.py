import re
from typing import Literal, Optional, TypeAlias, TypedDict

WhereOp: TypeAlias = Literal["AND", "OR"]
JoinOp: TypeAlias = Literal["INNER", "LEFT", "CROSS"]


class OnConflict(TypedDict):
  index: str
  action: str


class Query:
  def __init__(self):
    self._ctes: list[tuple[str, str]] = []
    self._select: list[str] = []
    self._table: Optional[str] = None
    self._joins: list[str] = []
    self._where: list[tuple[str, WhereOp]] = []
    self._order: Optional[str] = None
    self._limit: Optional[int] = None
    self._offset: Optional[int] = None
    self._params = []

  @property
  def columns(self) -> list[tuple[str, Optional[str]]]:
    as_regex = re.compile(r"\s+[Aa][Ss]\s+")
    result: list[tuple[str, Optional[str]]] = []
    for column in self._select:
      if as_regex.search(column):
        name, alias = as_regex.split(column)
        result.append((name.strip(), alias.strip()))
      else:
        result.append((column.strip(), None))

    return result

  def with_(self, name: str, query: "Query"):
    cte_sql, cte_params = query.build()
    self._ctes.append((name, cte_sql))
    self._params = cte_params + self._params
    return self

  def select(self, *cols: str):
    self._select.extend(cols)
    return self

  def from_(self, table: str, *values):
    self._table = table
    self._params = list(values) + self._params
    return self

  def join(self, table: str, on: Optional[str] = None, join_type: JoinOp = "INNER"):

    if join_type == "CROSS":
      if on is not None:
        raise ValueError("CROSS JOIN does not take an ON clause")
      self._joins.append(f"CROSS JOIN {table}")
    else:
      if on is None:
        raise ValueError(f"{join_type} JOIN requires an ON clause")

      self._joins.append(f"{join_type} JOIN {table} ON {on}")

    return self

  def inner_join(self, table: str, on: str):
    return self.join(table, on, join_type="INNER")

  def left_join(self, table: str, on: str):
    return self.join(table, on, join_type="LEFT")

  def cross_join(self, table: str):
    return self.join(table, join_type="CROSS")

  def where(self, condition: str, *values, op: WhereOp = "AND"):
    self._where.append((condition, op))
    self._params.extend(values)
    return self

  def where_group(
    self,
    *conditions: tuple[str, ...],
    op_inner: WhereOp = "OR",
    op_outer: WhereOp = "AND",
  ):
    parts = []
    for condition, *values in conditions:
      parts.append(condition)
      self._params.extend(values)

    grouped = "(" + f" {op_inner} ".join(parts) + ")"
    self._where.append((grouped, op_outer))

  def order_by(self, col: str):
    self._order = col
    return self

  def limit(self, n: int):
    if not isinstance(n, int) or n < -1:
      raise ValueError("Limit must be -1 or a non-negative integer")

    self._limit = n
    return self

  def offset(self, n: int):
    if not isinstance(n, int) or n < 0:
      raise ValueError("Offset must be a non-negative integer")

    self._offset = n
    return self

  def build(self):
    if not self._select:
      raise ValueError("No columns selected")

    if not self._table:
      raise ValueError("No table specified")

    sql: list[str] = []
    if self._ctes:
      cte_parts = [f"{name} AS ({cte_sql})" for name, cte_sql in self._ctes]
      sql.append("WITH " + ", ".join(cte_parts))

    sql += ["SELECT", ", ".join(self._select), "FROM", self._table]

    if self._joins:
      sql.append(" ".join(self._joins))

    if self._where:
      clauses = [self._where[0][0]]
      for condition, op in self._where[1:]:
        clauses.append(f"{op} {condition}")
      sql.append("WHERE " + " ".join(clauses))

    if self._order:
      sql.append("ORDER BY " + self._order)

    if self._limit is not None:
      sql.append(f"LIMIT {self._limit}")
      if self._offset is not None:
        sql.append(f"OFFSET {self._offset}")
    elif self._offset is not None:
      sql.extend(("LIMIT -1", f"OFFSET {self._offset}"))

    return " ".join(sql), self._params
