import { Typography } from "@mui/material";
import { useEffect, useState } from "react";
import Product from "./Product";
import { DataGrid } from "@mui/x-data-grid";
import { apiRequest } from "../../../api";

export default function Products() {
  const [products, setProducts] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();

    async function loadProducts() {
      try {
        const materials = await apiRequest("/materials", { signal: controller.signal });
        setProducts(materials);
      } catch (requestError) {
        if (requestError.name !== "AbortError") {
          setError(requestError.message || "Unable to load inventory. Check the API server and database.");
        }
      }
    }

    loadProducts();
    return () => controller.abort();
  }, []);

  const columns = [
    {
      field: "material_id",
      headerName: "ID",
      width: 90,
      description: "Material ID",
    },
    {
      field: "name",
      headerName: "Material",
      width: 260,
      description: "Material name",
      renderCell: (cellData) => {
        return <Product productName={cellData.row.name} />;
      },
    },
    {
      field: "type",
      headerName: "Category",
      width: 200,
      description: "Material category",
    },
    {
      field: "quantity_in_stock",
      headerName: "Quantity",
      width: 150,
      renderCell: ({ row }) => `${row.quantity_in_stock ?? 0} ${row.unit || ""}`,
    },
    {
      field: "reorder_level",
      headerName: "Minimum stock",
      width: 160,
    },
    {
      field: "unit_cost",
      headerName: "Unit cost",
      width: 140,
      renderCell: ({ row }) => `PHP ${row.unit_cost ?? 0}`,
    },
  ];

  return (
    <div>
      {error && <Typography color="error" sx={{ m: 2 }}>{error}</Typography>}
      <DataGrid
        sx={{ borderLeft: 0, borderRight: 0, borderRadius: 0 }}
        rows={products}
        getRowId={(row) => row.material_id}
        columns={columns}
        initialState={{
          pagination: {
            paginationModel: { page: 0, pageSize: 10 },
          },
        }}
        pageSizeOptions={[5, 10, 20]}
        checkboxSelection
      />
    </div>
  );
}
