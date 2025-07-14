import {GenericSerialFabricator} from '../models/serial_fabricator.js'
import db from'../config/db.js';

const getAllDevices = async (req, res) => {
    db.query('SELECT * FROM devices')
        .then(devices => {
            res.status(200).json({data: devices.map(device => new GenericSerialFabricator(device)), error: null});
        })
        .catch(err => {
            console.error('Error fetching devices:', err);
            res.status(500).json({data: null, error: 'Internal server error'});
        });
}

export default {
    getAllDevices
}