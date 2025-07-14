import jwt from "jsonwebtoken";
/** @typedef {import("express").Request} Request */
/** @typedef {import("express").Response} Response */
/** @typedef {import("express").NextFunction} NextFunction */

/**
 * Express middleware to verify JWT and check for the admin role.
 * @param {Request} req
 * @param {Response} res
 * @param {NextFunction} next
 * @returns {Promise<void>}
 */
export default async (req, res, next) => {
    const token = req.headers.authorization;

    if (!token) {
        res.status(401).send({data: null, error: "Token missing"});
        return;
    }
    try {
        const payload = await new Promise((resolve, reject) => {
            jwt.verify(token, process.env.JWT_SECRET || "super-secret-key", (err, decoded) => {
                if (err) return reject(err);
                return resolve(decoded);
            });
        });
        // Check if payload has id and role and if the role is admin
        if (!payload || !payload.id || !payload.role) {
            res.status(401).json({data: null, error: "Invalid token"});
            return;
        }
        if (payload.role !== "admin") {
            res.status(403).json({data: null, error: "admins only"});
            return;
        }
        next();
    } catch (err) {
        if (err instanceof Error && err.message === 'jwt expired') {
            res.status(401).json({data: null, message: "Token expired", error: err});
            return;
        }
        res.status(401).json({data: null, message: "Invalid token", error: err});
    }
};
