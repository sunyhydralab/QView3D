import express from 'express';

// Import auth middleware
import JWTHandler from "../middlewares/JWTHandler.js";
// Import the device controller
import userController from '../controllers/userController.js';

const router = express.Router();

// Define the routes for device management
router.get('/', userController.getAllUsers);

export default router;