import express from 'express';
import dotenv from 'dotenv';
import cors from 'cors';

// Import routes
import deviceRoutes from './src/routes/deviceRoutes.js';
import userRoutes from './src/routes/userRoutes.js';
import db from './src/config/db.js';
import ErrorHandler from './src/middlewares/ErrorHandler.js';
// Initialize dotenv for environment variables

dotenv.config();

// Initialize database connection
try {
    await db.query('SELECT 1');
    console.log('Database connection successful');
}
catch (error) {
    console.error('Database connection failed:', error);
    process.exit(1); // Exit the process if database connection fails
}

const PORT = process.env.PORT || 3000;

const app = express();

app.use(express.json());
app.use(cors());

app.get('/', (req, res) => {
    res.send('Welcome to the 3D Printer Device Management API');
});
// Use routes
app.use('/api/devices', deviceRoutes);
app.use('/api/users', userRoutes);
app.use(ErrorHandler);

app.listen(PORT, () => {
    console.log('Server is running on port', PORT);
});