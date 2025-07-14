import db from '../config/db.js';

const getAllUsers = async (req, res) => {
    return await db.query('SELECT * FROM users')
        .then(users => {
            res.status(200).json({data: users});
        })
        .catch(err => {
            res.status(500).json({error: err});
        });
}

export default {getAllUsers};