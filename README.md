# inventory management system using React + Vite (not completed yet !)

## Backend API

The dashboard's inventory table gets its data from the FastAPI server at `http://127.0.0.1:8000`. The backend uses PostgreSQL. Create a database named `inventory_management`, then copy `backend/.env.example` to `backend/.env` and set `DATABASE_URL` with your PostgreSQL credentials.

Open a second PowerShell terminal at the project root and run:

```powershell
python -m pip install -r backend\requirements.txt
Set-Location backend
python main.py
```

Keep the Vite development server running in the first terminal with `npm run dev`. The API documentation is available at `http://127.0.0.1:8000/docs`. Set `VITE_API_BASE_URL` to use a different API address.

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.
the grey color for testing margins and paddings

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react/README.md) uses [Babel](https://babeljs.io/) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh
- ### react libraries used in this app
- #### react Material UI
- #### react Router
- #### react Data Grid
- #### react Apex Charts
- #### react Material Icons
- ### Screen
  - ## Home
  ![click me](https://github.com/IMDADMI/inventory-management-system/blob/2-home-part/src/assets/Home.PNG?raw=true)
  - ## Inventory
  ![click me](https://github.com/IMDADMI/inventory-management-system/blob/3-inventory-part/src/assets/Home.PNG?raw=true)
  - ## order 
  ![click me](https://github.com/IMDADMI/inventory-management-system/blob/4-order-part/src/assets/Home.PNG?raw=true)
  - ## order modal
  ![click me](https://github.com/IMDADMI/inventory-management-system/blob/4-order-part-2/src/assets/Home.PNG?raw=true)
  - ## Customer
  ![click me](https://github.com/IMDADMI/inventory-management-system/blob/5-customer-part/src/assets/Home.PNG?raw=true)
 - ## Revenue
  ![click me](https://github.com/IMDADMI/inventory-management-system/blob/6-revenue-part/src/assets/Home.PNG?raw=true)
  - ## Growth
  ![click me](https://github.com/IMDADMI/inventory-management-system/blob/7-growth-part/src/assets/Home.PNG?raw=true)
