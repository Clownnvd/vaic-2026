import pyarrow.parquet as pq

pf = pq.ParquetFile("./data/_probe.parquet")
print("rows:", pf.metadata.num_rows, "| row_groups:", pf.num_row_groups)
for f in pf.schema_arrow:
    print(f"  {f.name:22} {f.type}")
