import re
from typing import Any, Literal, Optional, TypeAlias

WhereOp: TypeAlias = Literal["AND", "OR"]
JoinOp: TypeAlias = Literal["INNER", "LEFT", "CROSS"]
SortOrder: TypeAlias = Literal["asc", "desc"]


class DeleteQuery:
  def __init__(self):
    self._table: Optional[str] = None
    self._where: list[tuple[str, WhereOp]] = []
    self._where_params: list[Any] = []
    self._returning: list[str] = []

  def from_(self, table: str):
    self._table = table
    return self

  def where(self, condition: str, *values: Any, op: WhereOp = "AND"):
    self._where.append((condition, op))
    self._where_params.extend(values)
    return self

  def returning(self, *cols: str):
    self._returning.extend(cols)
    return self

  def build(self) -> tuple[str, list[Any]]:
    if not self._table:
      raise ValueError("No table specified")

    sql: list[str] = ["DELETE FROM", self._table]
    params: list[Any] = []

    if self._where:
      clauses = [self._where[0][0]]
      for condition, op in self._where[1:]:
        clauses.append(f"{op} {condition}")

      sql.append("WHERE " + " ".join(clauses))
      params.extend(self._where_params)

    if self._returning:
      sql.append("RETURNING " + ", ".join(self._returning))

    return " ".join(sql), params


class UpdateQuery:
  def __init__(self):
    self._table: Optional[str] = None
    self._set: list[str] = []
    self._set_params: list[Any] = []
    self._from: Optional[str] = None
    self._where: list[tuple[str, WhereOp]] = []
    self._where_params: list[Any] = []
    self._returning: list[str] = []

  def table(self, table: str):
    self._table = table
    return self

  def set(self, column: str, value: Any):
    self._set.append(f"{column} = ?")
    self._set_params.append(value)
    return self

  def set_raw(self, assignment: str, *values: Any):
    self._set.append(assignment)
    self._set_params.extend(values)
    return self

  def set_excluded(self, *cols: str):
    self._set.extend(f"{c} = excluded.{c}" for c in cols)
    return self

  def from_(self, table: str):
    self._from = table
    return self

  def where(self, condition: str, *values: Any, op: WhereOp = "AND"):
    self._where.append((condition, op))
    self._where_params.extend(values)
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
      self._where_params.extend(values)

    grouped = "(" + f" {op_inner} ".join(parts) + ")"
    self._where.append((grouped, op_outer))
    return self

  def returning(self, *cols: str):
    self._returning.extend(cols)
    return self

  def _build_set_clause(self) -> tuple[str, list[Any]]:
    if not self._set:
      raise ValueError("No columns to update")
    return ", ".join(self._set), self._set_params

  def _build_where_clause(self) -> tuple[Optional[str], list[Any]]:
    if not self._where:
      return None, []

    clauses = [self._where[0][0]]
    for condition, op in self._where[1:]:
      clauses.append(f"{op} {condition}")
    return " ".join(clauses), list(self._where_params)

  def build(self) -> tuple[str, list[Any]]:
    if not self._table:
      raise ValueError("No table specified")

    set_sql, params = self._build_set_clause()
    sql: list[str] = ["UPDATE", self._table, "SET", set_sql]

    if self._from:
      sql.append(f"FROM {self._from}")

    where_sql, where_params = self._build_where_clause()
    if where_sql:
      sql.append(f"WHERE {where_sql}")
      params.extend(where_params)

    if self._returning:
      sql.append("RETURNING " + ", ".join(self._returning))

    return " ".join(sql), params


class InsertQuery:
  def __init__(self):
    self._table: Optional[str] = None
    self._columns: list[str] = []
    self._value_rows: list[str] = []
    self._value_params: list[Any] = []
    self._select_sql: Optional[str] = None
    self._select_params: list[Any] = []
    self._conflict_target: list[str] = []
    self._conflict_where: Optional[str] = None
    self._update_query: Optional[UpdateQuery] = None
    self._action: Optional[Literal["NOTHING", "UPDATE"]] = None
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

  def values_placeholders(self, *placeholders: str):
    self._value_rows.append(f"({', '.join(placeholders)})")
    return self

  def from_select(self, select_query: "SelectQuery"):
    if self._columns and len(select_query.columns) != len(self._columns):
      raise ValueError(
        f"Expected {len(self._columns)} selected columns, got {len(select_query.columns)}"
      )

    self._select_sql, self._select_params = select_query.build()
    return self

  def on_conflict(self, *target_cols: str, where: Optional[str] = None):
    self._conflict_target.extend(target_cols)
    self._conflict_where = where
    return self

  def do_nothing(self):
    self._action = "NOTHING"
    return self

  def do_update(self, update: UpdateQuery):
    self._action = "UPDATE"
    self._update_query = update
    return self

  def returning(self, *cols: str):
    self._returning.extend(cols)
    return self

  def build(self) -> tuple[str, list[Any]]:
    if not self._table:
      raise ValueError("No table specified")

    if not self._columns:
      raise ValueError("No columns specified")

    if not self._value_rows and self._select_sql is None:
      raise ValueError("No values specified")

    if self._select_sql is not None:
      if self._value_rows:
        raise ValueError("Cannot use both values() and from_select()")

      sql = [
        "INSERT INTO",
        self._table,
        f"({', '.join(self._columns)})",
        self._select_sql,
      ]
      params = list(self._select_params)

    else:
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
        if self._update_query is None:
          raise ValueError("DO UPDATE requires an UpdateQuery passed to do_update()")

        set_sql, set_params = self._update_query._build_set_clause()
        sql.append("DO UPDATE SET " + set_sql)
        params.extend(set_params)

        where_sql, where_params = self._update_query._build_where_clause()
        if where_sql:
          sql.append(f"WHERE {where_sql}")
          params.extend(where_params)
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
    self._select_params: list[Any] = []
    self._table: Optional[str] = None
    self._joins: list[str] = []
    self._where: list[tuple[str, WhereOp]] = []
    self._group_by: list[str] = []
    self._having: list[tuple[str, WhereOp]] = []
    self._order: list[str] = []
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

  def with_(self, name: str, query: "SelectQuery"):
    cte_sql, cte_params = query.build()
    self._ctes.append((name, cte_sql))
    self._params = cte_params + self._params
    return self

  def select(self, *cols: str):
    self._select.extend(cols)
    return self

  def select_raw(self, expr: str, *values, Any, alias: Optional[str] = None):
    self._select.append(f"{expr} AS {alias}" if alias else expr)
    self._select_params.extend(values)
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
    self._order.append(f"{col} {direction.upper()}")
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
      sql.append("ORDER BY " + ", ".join(self._order))

    if self._limit is not None:
      sql.append(f"LIMIT {self._limit}")
      if self._offset is not None:
        sql.append(f"OFFSET {self._offset}")
    elif self._offset is not None:
      sql.extend(("LIMIT -1", f"OFFSET {self._offset}"))

    return " ".join(sql), self._select_params + self._params


class UnionQuery:
  def __init__(
    self,
    *queries: SelectQuery,
    union_type: Literal["UNION", "UNION ALL"] = "UNION ALL",
    cte: Optional[SelectQuery] = None,
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
