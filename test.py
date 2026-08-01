from src.bootstrap import get_settings, load_env
from src.hashing import decode_sha256_from_b64
from src.sqlite.connect import SqliteDatabase

if __name__ == "__main__":
  load_env()
  app_settings = get_settings()

  image_id = decode_sha256_from_b64("N5Cmu4MkV0vjxw5aI039wgFYDzm0-hFfs1UIGEhRC7E")

  with SqliteDatabase(app_settings.LOCATION_DB, spatial=True) as db:
    cursor = db.conn.cursor()
    cursor.execute(f"ATTACH DATABASE '{app_settings.INDEX_DB}' AS i")

    cursor.execute(
      """
          EXPLAIN QUERY PLAN
          SELECT areas.name, AsGeoJSON(areas.geometry)
          FROM areas
          WHERE ST_Intersects(areas.geometry, (SELECT footprint FROM i.images WHERE id = ?))
          """,
      (image_id,),
    )
    for row in cursor.fetchall():
      print(row)

    cursor.execute("DETACH DATABASE i")
