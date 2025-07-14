import express from "express";
// Import the device controller
import deviceController from "../controllers/deviceController.js";
// Import auth middleware
import JWTHandler from "../middlewares/JWTHandler.js";

const router = express.Router();

// Define the routes for device management\
router.get('/', JWTHandler, deviceController.getAllDevices);

export default router;