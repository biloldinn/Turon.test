const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const multer = require('multer');
const path = require('path');
const http = require('http');
const socketIo = require('socket.io');
const fs = require('fs');
const axios = require('axios');
const pdf = require('pdf-parse');
require('dotenv').config();

const app = express();
const server = http.createServer(app);
const io = socketIo(server, {
    cors: { origin: "*", methods: ["GET", "POST"] },
    pingTimeout: 60000,
    pingInterval: 25000
});

const PORT = process.env.PORT || 5000;

app.use(cors());
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true, limit: '50mb' }));
app.use(express.static('.'));

// MongoDB connection
const MONGODB_URI = process.env.MONGODB_URI;

mongoose.connect(MONGODB_URI, {
    useNewUrlParser: true,
    useUnifiedTopology: true,
})
    .then(() => console.log('✅ MongoDB muvaffaqiyatli ulandi'))
    .catch(err => console.error('❌ MongoDB ulanish xatosi:', err.message));

// Schemas
const userSchema = new mongoose.Schema({
    firstName: { type: String, required: true },
    lastName: { type: String, required: true },
    phone: { type: String, unique: true, required: true },
    password: { type: String, required: true },
    groupCode: { type: String, required: true },
    role: { type: String, default: 'student', enum: ['student', 'admin'] },
    createdAt: { type: Date, default: Date.now }
});

const testSchema = new mongoose.Schema({
    title: { type: String, required: true },
    courseName: { type: String, default: 'Umumiy' },
    description: String,
    questions: { type: Array, required: true },
    timeLimit: { type: Number, default: 30 },
    totalScore: { type: Number, default: 100 },
    startTime: { type: Date, default: Date.now },
    endTime: { type: Date, default: () => new Date(Date.now() + 7 * 24 * 60 * 60 * 1000) },
    groupCode: { type: String, required: true },
    createdBy: { type: mongoose.Schema.Types.ObjectId, ref: 'User' },
    createdAt: { type: Date, default: Date.now }
});

const resultSchema = new mongoose.Schema({
    userId: { type: mongoose.Schema.Types.ObjectId, ref: 'User' },
    testId: { type: mongoose.Schema.Types.ObjectId, ref: 'Test' },
    answers: Array,
    score: Number,
    totalScore: Number,
    percentage: Number,
    passed: Boolean,
    grade: { type: Number, default: 0 },
    timeTaken: Number,
    submittedAt: { type: Date, default: Date.now }
});

const activitySchema = new mongoose.Schema({
    userId: { type: mongoose.Schema.Types.ObjectId, ref: 'User' },
    userName: String,
    activity: String,
    testTitle: String,
    score: Number,
    timestamp: { type: Date, default: Date.now }
});

const User = mongoose.model('User', userSchema);
const Test = mongoose.model('Test', testSchema);
const Result = mongoose.model('Result', resultSchema);
const Activity = mongoose.model('Activity', activitySchema);

// Multer
const storage = multer.diskStorage({
    destination: (dir, file, cb) => {
        if (!fs.existsSync('./uploads')) fs.mkdirSync('./uploads', { recursive: true });
        cb(null, './uploads');
    },
    filename: (req, file, cb) => {
        cb(null, Date.now() + '-' + file.originalname);
    }
});
const upload = multer({ storage });

// Helper
async function logActivity(userId, activity, details = {}) {
    try {
        const user = await User.findById(userId);
        const log = new Activity({
            userId,
            userName: user ? `${user.firstName} ${user.lastName}` : 'System',
            activity,
            ...details
        });
        await log.save();
        io.emit('activity_update', log);
    } catch (e) { }
}

// API Routes
app.post('/api/login', async (req, res) => {
    try {
        const { phone, password } = req.body;
        const ADMIN_PHONE = process.env.ADMIN_PHONE || 'Biloldin';
        const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || 'bilol006';

        let user;
        if (phone === ADMIN_PHONE && password === ADMIN_PASSWORD) {
            user = await User.findOne({ phone: ADMIN_PHONE });
            if (!user) {
                user = new User({
                    firstName: 'Biloldin',
                    lastName: 'Admin',
                    phone: ADMIN_PHONE,
                    password: ADMIN_PASSWORD,
                    role: 'admin',
                    groupCode: 'ADMIN'
                });
                await user.save();
            }
        } else {
            user = await User.findOne({ phone, password });
        }

        if (!user) return res.status(401).json({ success: false, error: 'Login yoki parol xato' });

        logActivity(user._id, user.role === 'admin' ? 'admin_login' : 'student_login');
        res.json({ success: true, user: { id: user._id, firstName: user.firstName, lastName: user.lastName, phone: user.phone, role: user.role, groupCode: user.groupCode } });
    } catch (e) {
        res.status(500).json({ success: false, error: e.message });
    }
});

app.post('/api/register', async (req, res) => {
    try {
        const { firstName, lastName, phone, groupCode, password } = req.body;
        const existing = await User.findOne({ phone });
        if (existing) return res.json({ success: false, error: 'Bu raqam band' });

        const user = new User({ firstName, lastName, phone, groupCode, password });
        await user.save();
        logActivity(user._id, 'registration');
        res.json({ success: true });
    } catch (e) { res.status(500).json({ success: false, error: e.message }); }
});

// Student
app.get('/api/tests/student/:groupCode', async (req, res) => {
    try {
        const tests = await Test.find({ groupCode: req.params.groupCode }).lean().sort({ createdAt: -1 });
        const userId = req.headers['user-id'];
        for (let test of tests) {
            const result = await Result.findOne({ userId, testId: test._id });
            test.isTaken = !!result;
        }
        res.json({ success: true, tests });
    } catch (e) { res.status(500).json({ success: false, error: e.message }); }
});

app.get('/api/results/student', async (req, res) => {
    try {
        const userId = req.headers['user-id'];
        const results = await Result.find({ userId }).populate('testId').sort({ submittedAt: -1 });
        res.json({ success: true, results });
    } catch (e) { res.status(500).json({ success: false, error: e.message }); }
});

app.get('/api/tests/take/:testId', async (req, res) => {
    try {
        const test = await Test.findById(req.params.testId);
        res.json({ success: true, test });
    } catch (e) { res.status(500).json({ success: false, error: e.message }); }
});

app.post('/api/tests/submit', async (req, res) => {
    try {
        const { testId, answers, timeTaken } = req.body;
        const userId = req.headers['user-id'];
        const test = await Test.findById(testId);
        if (!test) return res.status(404).json({ success: false, error: 'Test topilmadi' });

        let score = 0;
        const processedAnswers = [];
        test.questions.forEach((q, i) => {
            const isCorrect = q.correctAnswer === answers[i];
            const qScore = q.score || 5;
            if (isCorrect) score += qScore;
            processedAnswers.push({ question: q.text, selected: answers[i], correct: q.correctAnswer, isCorrect, score: isCorrect ? qScore : 0 });
        });

        const totalScore = test.totalScore || 100;
        const percentage = Math.round((score / totalScore) * 100);
        const passed = percentage >= 60;

        const result = new Result({ userId, testId, answers: processedAnswers, score, totalScore, percentage, passed, timeTaken });
        await result.save();
        logActivity(userId, 'test_completed', { testTitle: test.title, score: percentage });
        res.json({ success: true, score, totalScore, percentage, passed });
    } catch (e) { res.status(500).json({ success: false, error: e.message }); }
});

// Admin
app.get('/api/admin/dashboard', async (req, res) => {
    try {
        const stats = {
            students: await User.countDocuments({ role: 'student' }),
            tests: await Test.countDocuments(),
            results: await Result.countDocuments(),
            files: fs.existsSync('./uploads') ? fs.readdirSync('./uploads').length : 0,
            todayResults: await Result.countDocuments({ submittedAt: { $gte: new Date().setHours(0, 0, 0, 0) } })
        };
        const recentActivities = await Activity.find().sort({ timestamp: -1 }).limit(20);
        res.json({ success: true, stats, recentActivities });
    } catch (e) { res.status(500).json({ success: false, error: e.message }); }
});

app.get('/api/admin/students', async (req, res) => {
    try {
        const students = await User.find({ role: 'student' }).sort({ groupCode: 1, firstName: 1 });
        res.json({ success: true, students });
    } catch (e) { res.status(500).json({ success: false, error: e.message }); }
});

app.post('/api/admin/tests/create', async (req, res) => {
    try {
        const { title, courseName, description, questions, timeLimit, groupCode } = req.body;
        const totalScore = questions.reduce((sum, q) => sum + (q.score || 5), 0);
        const test = new Test({ title, courseName, description, questions, timeLimit, totalScore, groupCode, createdBy: req.headers['user-id'] });
        await test.save();
        res.json({ success: true, testId: test._id });
    } catch (e) { res.status(500).json({ success: false, error: e.message }); }
});

app.get('/api/admin/tests', async (req, res) => {
    try {
        const tests = await Test.find().sort({ createdAt: -1 });
        res.json({ success: true, tests });
    } catch (e) { res.status(500).json({ success: false, error: e.message }); }
});

app.get('/api/admin/results', async (req, res) => {
    try {
        const results = await Result.find().populate('userId').populate('testId').sort({ submittedAt: -1 });
        res.json({ success: true, results });
    } catch (e) { res.status(500).json({ success: false, error: e.message }); }
});

app.get('/api/admin/list', async (req, res) => {
    try {
        const admins = await User.find({ role: 'admin' }).sort({ createdAt: -1 });
        res.json({ success: true, admins });
    } catch (e) { res.status(500).json({ success: false, error: e.message }); }
});

app.post('/api/admin/create', async (req, res) => {
    try {
        const { firstName, lastName, phone, password } = req.body;
        const admin = new User({ firstName, lastName, phone, password, role: 'admin', groupCode: 'ADMIN' });
        await admin.save();
        res.json({ success: true });
    } catch (e) { res.status(500).json({ success: false, error: e.message }); }
});

app.delete('/api/admin/delete/:id', async (req, res) => {
    try {
        await User.findByIdAndDelete(req.params.id);
        res.json({ success: true });
    } catch (e) { res.status(500).json({ success: false, error: e.message }); }
});

// Socket.io
const onlineUsers = new Map();
io.on('connection', (socket) => {
    const { userId, userName, role, groupCode } = socket.handshake.query;
    if (userId) {
        onlineUsers.set(userId, { id: userId, name: userName, role, groupCode, status: 'online', socketId: socket.id });
        io.emit('online_students', Array.from(onlineUsers.values()));
    }
    socket.on('test_started', (data) => {
        if (onlineUsers.has(data.studentId)) {
            onlineUsers.get(data.studentId).status = 'testing';
            io.emit('online_students', Array.from(onlineUsers.values()));
        }
    });
    socket.on('screen_update', (data) => io.emit('screen_mirror_update', data));
    socket.on('disconnect', () => {
        onlineUsers.delete(userId);
        io.emit('online_students', Array.from(onlineUsers.values()));
    });
});

server.listen(PORT, () => console.log(`🚀 Server on port ${PORT}`));
