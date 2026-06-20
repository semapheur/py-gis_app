import re
from typing import Any, Literal, Optional, TypeAlias, TypedDict

WhereOp: TypeAlias = Literal["AND", "OR"]
JoinOp: TypeAlias = Literal["INNER", "LEFT", "CROSS"]
SortOrder: TypeAlias = Literal["asc", "desc"]


class OnConflict(TypedDict):
  index: str
  action: str


class InsertQuery:
  def __init__(self):
    self._table: Optional[str] = None
    self._columns: list[str] = []
    self._value_rows: list[str] = []
    self._value_params: list[Any] = []
    self.conflict_target: list[str] = []
    self._action: Optional[Literal["NOTHING", "UPDATE"]] = None
    self._update_set: list[str] = []
    self._update_params: list[Any] = []
    self._update_where: list[tuple[str, WhereOp]] = []
    self._update_where_params: list[Any] = []
    self._returning: list[str] = []

    def into(self, table: str):
      self._table = table
      return self

    def columns(self, *cols: str):
      self._columns.extend(cols)
      return self

    def values(self, *values: Any):
      if self._columns and len(values) != len(self._columns):
        raise ValueError(f"Expected {len(self._columns)} values, got {len(values)}")

      placeholders = ", ".join(["?"] * len(values))
      self._value_rows.append(f"({placeholders})")
      self._value_params.extend(values)
      return self

    def on_conflict(self, *target_cols: str, where: Optional[str] = None):
      self._conflict_target.extend(target_cols)
      self._conflict_where = where
      return self

    def do_nothing(self):
      self._action = "NOTHING"
      return self

    def do_update(self, *assignments: str):
      self._action = "UPDATE"
      self._update_set.extend(assignments)
      return self

    def self_value(self, column: str, value: Any):
      self._action = "UPDATE"
      self._update_set.append(f"{column} = ?")
      self._update_params.append(value)
      return self

    def where(self, condition: str, *values: Any, op: WhereOp = "AND"):
      self._update_where.append((condition, op))
      self._update_where_params.extend(values)
      return self

    def returning(self, *cols, str):
      self._returning.extend(cols)
      return self

    def build(self) -> tuple[str, list[Any]]:
      if not self._table:
        raise ValueError("No table specified")

      if not self._columns:
        raise ValueError("No columns specified")

      if not self._value_rows:
        raise ValueError("No values specified")

      sql = [
        "INSERT INTO",
        self._table,
        f"({', '.join(self._columns)})",
        "VALUES",
        ", ".join(self._value_rows),
      ]
      params = list(self._value_params)

      if self._conflict_target or self._action:
        conflict_clause = "ON CONFLICT"
        if self._conflict_target:
          conflict_clause += f" ({', '.join(self._conflict_target)})"
        if self._conflict_where:
          conflict_clause += f" WHERE {self._conflict_where}"
        sql.append(conflict_clause)

        if self._action == "NOTHING":
          sql.append("DO NOTHING")

        elif self._action == "UPDATE":
          if not self._update_set:
            raise ValueError("DO UPDATE requires at least one SET assignment")

          sql.append("DO UPDATE SET " + ", ".join(self._update_set))
          params.extend(self._update_params)

          if self._update_where:
            clauses = [self._update_where[0][0]]
            for condition, op in self._update_where[1:]:
              clauses.append(f"{op} {condition}")
            sql.append("WHERE" + " ".join(clauses))
            params.extend(self._update_where_params)
          else:
            raise ValueError(
              "on_conflict() requires do_nothing() or do_update() to be called"
            )

      if self._returning:
        sql.append("RETURNING " + ", ".join(self._returning))

      return " ".join(sql), params


class SelectQuery:
  def __init__(self):
    self._ctes: list[tuple[str, str]] = []
    self._select: list[str] = []
    self._table: Optional[str] = None
    self._joins: list[str] = []
    self._where: list[tuple[str, WhereOp]] = []
    self._group_by: list[str] = []
    self._having: list[tuple[str, WhereOp]] = []
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
    *conditions: tuple[str, Any],
    op_inner: WhereOp = "OR",
    op_outer: WhereOp = "AND",
  ):
    parts = []
    for condition, *values in conditions:
      parts.append(condition)
      self._params.extend(values)

    grouped = "(" + f" {op_inner} ".join(parts) + ")"
    self._where.append((grouped, op_outer))

  def group_by(self, *cols: str):
    self._group_by.extend(cols)
    return self

  def having(self, condition: str, *values, op: WhereOp = "AND"):
    self._having.append((condition, op))
    self._params.extend(values)
    return self

  def order_by(self, col: str, direction: SortOrder = "asc"):
    self._order = f"{col} {direction.upper()}"
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

    if self._group_by:
      sql.append("GROUP BY " + ", ".join(self._group_by))

    if self._having:
      clauses = [self._having[0][0]]
      for condition, op in self._having[1:]:
        clauses.append(f"{op} {condition}")

      sql.append("HAVING " + " ".join(clauses))

    if self._order:
      sql.append("ORDER BY " + self._order)

    if self._limit is not None:
      sql.append(f"LIMIT {self._limit}")
      if self._offset is not None:
        sql.append(f"OFFSET {self._offset}")
    elif self._offset is not None:
      sql.extend(("LIMIT -1", f"OFFSET {self._offset}"))

    return " ".join(sql), self._params


class UnionQuery:
  def __init__(
    self,
    *queries: Query,
    union_type: Literal["UNION", "UNION ALL"] = "UNION ALL",
    cte: Optional[Query] = None,
    cte_name: Optional[str] = None,
  ):
    self._queries = queries
    self._cte = cte
    self._cte_name = cte_name
    self._union_type = union_type
    self._order: Optional[str] = None
    self._limit: Optional[int] = None
    self._offset: Optional[int] = None

  def order_by(self, col: str, direction: SortOrder = "asc"):
    self._order = f"{col} {direction.upper()}"
    return self

  def limit(self, n: int):
    self._limit = n
    return self

  def offset(self, n: int):
    self._offset = n
    return self

  def build(self):
    parts = []
    all_params = []

    cte_sql = None
    if self._cte and self._cte_name:
      cte_sql, cte_params = self._cte.build()
      all_params.extend(cte_params)

    for query in self._queries:
      sql, params = query.build()
      parts.append(sql)
      all_params.extend(params)

    union_sql = f" {self._union_type} ".join(parts)
    if self._cte is not None:
      union_sql = f"WITH {self._cte_name} AS ({cte_sql}) {union_sql}"

    if self._order:
      union_sql += f" ORDER BY {self._order}"

    if self._limit is not None:
      union_sql += f" LIMIT {self._limit}"

      if self._offset is not None:
        union_sql += f" OFFSET {self._offset}"

    elif self._offset is not None:
      union_sql += f"LIMIT -1 OFFSET {self._offset}"

    return union_sql, all_params
