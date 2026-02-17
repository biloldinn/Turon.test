const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const axios = require('axios');
const http = require('http');
const socketIo = require('socket.io');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
require('dotenv').config();

const app = express();
const server = http.createServer(app);
const io = socketIo(server, {
    cors: {
        origin: "*",
        methods: ["GET", "POST"]
    }
});

const PORT = process.env.PORT || 5000;
const MONGODB_URI = process.env.MONGODB_URI;
const JWT_SECRET = process.env.JWT_SECRET;

// Middleware
app.use(cors());
app.use(express.json());
app.use('/uploads', express.static(path.join(__dirname, 'uploads')));

// Ensure uploads directory exists
if (!fs.existsSync('./uploads')) {
    fs.mkdirSync('./uploads');
}

// MongoDB Connection
mongoose.connect(MONGODB_URI, {
    useNewUrlParser: true,
    useUnifiedTopology: true,
})
.then(() => console.log('✅ MongoDB connected successfully'))
.catch(err => console.error('❌ MongoDB connection error:', err));

// --- SCHEMAS ---

const userSchema = new mongoose.Schema({
    firstName: String,
    lastName: String,
    phone: { type: String, unique: true },
    password: { type: String, required: true },
    groupCode: String,
    role: { type: String, default: 'student' }, // 'admin' or 'student'
    createdAt: { type: Date, default: Date.now }
});

const testSchema = new mongoose.Schema({
    title: String,
    description: String,
    questions: [{
        text: String,
        options: [String],
        correctAnswer: String,
        score: { type: Number, default: 5 },
        createdByAI: { type: Boolean, default: false }
    }],
    timeLimit: { type: Number, default: 30 }, // in minutes
    totalScore: Number,
    groupCode: String,
    startTime: Date,
    endTime: Date,
    createdBy: { type: mongoose.Schema.Types.ObjectId, ref: 'User' },
    createdAt: { type: Date, default: Date.now }
});

const resultSchema = new mongoose.Schema({
    userId: { type: mongoose.Schema.Types.ObjectId, ref: 'User' },
    testId: { type: mongoose.Schema.Types.ObjectId, ref: 'Test' },
    score: Number,
    totalScore: Number,
    percentage: Number,
    passed: Boolean,
    timeTaken: Number, // in seconds
    answers: [{
        question: String,
        selected: String,
        correct: String,
        isCorrect: Boolean,
        score: Number
    }],
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

// --- AUTH API ---

app.post('/api/register', async (req, res) => {
    try {
        const { firstName, lastName, phone, groupCode, password } = req.body;
        const existingUser = await User.findOne({ phone });
        if (existingUser) return res.status(400).json({ success: false, error: 'Bu telefon raqami allaqachon ro\'yxatdan o\'tgan' });

        const hashedPassword = await bcrypt.hash(password, 10);
        const user = new User({ firstName, lastName, phone, groupCode, password: hashedPassword });
        await user.save();

        await logActivity(user._id, `${firstName} ${lastName}`, 'registration');
        res.json({ success: true });
    } catch (err) {
        res.status(500).json({ success: false, error: err.message });
    }
});

app.post('/api/login', async (req, res) => {
    try {
        const { phone, password } = req.body;
        
        // Admin override for demo/initial setup
        if (phone === 'admin' && password === process.env.ADMIN_PASSWORD) {
            let admin = await User.findOne({ phone: 'admin' });
            if (!admin) {
                admin = new User({ firstName: 'Admin', lastName: 'Turon', phone: 'admin', password: await bcrypt.hash(password, 10), role: 'admin' });
                await admin.save();
            }
            const token = jwt.sign({ id: admin._id, role: 'admin' }, JWT_SECRET);
            return res.json({ success: true, token, user: { id: admin._id, firstName: 'Admin', lastName: 'Turon', role: 'admin' } });
        }

        const user = await User.findOne({ phone });
        if (!user) return res.status(400).json({ success: false, error: 'Foydalanuvchi topilmadi' });

        const isMatch = await bcrypt.compare(password, user.password);
        if (!isMatch) return res.status(400).json({ success: false, error: 'Parol noto\'g\'ri' });

        const token = jwt.sign({ id: user._id, role: user.role }, JWT_SECRET);
        await logActivity(user._id, `${user.firstName} ${user.lastName}`, user.role === 'admin' ? 'admin_login' : 'student_login');

        res.json({ 
            success: true, 
            token, 
            user: { 
                id: user._id, 
                firstName: user.firstName, 
                lastName: user.lastName, 
                phone: user.phone, 
                groupCode: user.groupCode, 
                role: user.role 
            } 
        });
    } catch (err) {
        res.status(500).json({ success: false, error: err.message });
    }
});

// --- TEST API ---

app.get('/api/tests/student/:groupCode', async (req, res) => {
    try {
        const { groupCode } = req.params;
        const userId = req.headers['user-id'];
        
        const tests = await Test.find({ groupCode }).sort({ createdAt: -1 });
        const results = await Result.find({ userId });
        
        const testWithStatus = tests.map(test => {
            const result = results.find(r => r.testId.toString() === test._id.toString());
            return {
                ...test.toObject(),
                isTaken: !!result,
                result: result ? { score: result.score, percentage: result.percentage } : null
            };
        });

        res.json({ success: true, tests: testWithStatus });
    } catch (err) {
        res.status(500).json({ success: false, error: err.message });
    }
});

app.get('/api/tests/take/:testId', async (req, res) => {
    try {
        const test = await Test.findById(req.params.testId);
        if (!test) return res.status(404).json({ success: false, error: 'Test topilmadi' });
        
        // Hide correct answers when sending to student
        const safeTest = test.toObject();
        safeTest.questions.forEach(q => delete q.correctAnswer);
        
        res.json({ success: true, test: safeTest });
    } catch (err) {
        res.status(500).json({ success: false, error: err.message });
    }
});

app.post('/api/tests/submit', async (req, res) => {
    try {
        const { testId, answers, timeTaken } = req.body;
        const userId = req.headers['user-id'];
        
        const test = await Test.findById(testId);
        if (!test) return res.status(404).json({ success: false, error: 'Test topilmadi' });
        
        const user = await User.findById(userId);

        let score = 0;
        const questionResults = test.questions.map((q, idx) => {
            const isCorrect = q.correctAnswer === answers[idx];
            if (isCorrect) score += q.score;
            return {
                question: q.text,
                selected: answers[idx],
                correct: q.correctAnswer,
                isCorrect,
                score: isCorrect ? q.score : 0
            };
        });

        const percentage = Math.round((score / test.totalScore) * 100);
        const result = new Result({
            userId,
            testId,
            score,
            totalScore: test.totalScore,
            percentage,
            passed: percentage >= 60,
            timeTaken,
            answers: questionResults
        });

        await result.save();
        await logActivity(userId, `${user.firstName} ${user.lastName}`, 'test_completed', test.title, percentage);

        res.json({ success: true, score, totalScore: test.totalScore, percentage, passed: percentage >= 60 });
    } catch (err) {
        res.status(500).json({ success: false, error: err.message });
    }
});

// --- ADMIN API ---

app.get('/api/admin/dashboard', async (req, res) => {
    try {
        const stats = {
            students: await User.countDocuments({ role: 'student' }),
            tests: await Test.countDocuments(),
            results: await Result.countDocuments(),
            files: 0 // Placeholder for uploaded files
        };
        const recentActivities = await Activity.find().sort({ timestamp: -1 }).limit(10);
        res.json({ success: true, stats, recentActivities });
    } catch (err) {
        res.status(500).json({ success: false, error: err.message });
    }
});

app.post('/api/admin/tests/create', async (req, res) => {
    try {
        const { title, description, questions, timeLimit, groupCode, startTime, endTime } = req.body;
        const totalScore = questions.reduce((acc, q) => acc + (q.score || 5), 0);
        
        const test = new Test({
            title, description, questions, timeLimit, groupCode, totalScore,
            startTime: startTime || new Date(),
            endTime: endTime || new Date(Date.now() + 7 * 24 * 60 * 60 * 1000)
        });
        
        await test.save();
        res.json({ success: true, test });
    } catch (err) {
        res.status(500).json({ success: false, error: err.message });
    }
});

// AI Generation Endpoint
app.post('/api/admin/tests/generate-ai', async (req, res) => {
    try {
        const { topic, count, difficulty } = req.body;
        const prompt = `Create ${count} multiple choice questions about "${topic}" with difficulty "${difficulty}". 
        Return ONLY a JSON array of objects with fields: text, options (array of 4 strings), correctAnswer (string matching one of options), score (number).`;

        const response = await axios.post('https://api.deepseek.com/v1/chat/completions', {
            model: "deepseek-chat",
            messages: [{ role: "user", content: prompt }],
            response_format: { type: "json_object" }
        }, {
            headers: { 'Authorization': `Bearer ${process.env.DEEPSEEK_API_KEY}` }
        });

        const content = response.data.choices[0].message.content;
        const parsed = JSON.parse(content);
        const questions = Array.isArray(parsed) ? parsed : (parsed.questions || []);

        res.json({ success: true, questions });
    } catch (err) {
        console.error('AI Error:', err);
        res.status(500).json({ success: false, error: 'AI tests generation failed' });
    }
});

app.get('/api/results/student', async (req, res) => {
    try {
        const userId = req.headers['user-id'];
        const results = await Result.find({ userId }).populate('testId').sort({ submittedAt: -1 });
        res.json({ success: true, results });
    } catch (err) {
        res.status(500).json({ success: false, error: err.message });
    }
});

app.get('/api/results/:id', async (req, res) => {
    try {
        const result = await Result.findById(req.params.id).populate('testId');
        res.json({ success: true, result });
    } catch (err) {
        res.status(500).json({ success: false, error: err.message });
    }
});

// --- HELPER FUNCTIONS ---

async function logActivity(userId, userName, activity, testTitle = null, score = null) {
    try {
        const log = new Activity({ userId, userName, activity, testTitle, score });
        await log.save();
    } catch (err) {
        console.error('Logging error:', err);
    }
}

// --- SOCKET.IO LOGIC ---

const onlineUsers = new Map();

io.on('connection', (socket) => {
    const { userId, userName, role, groupCode } = socket.handshake.query;
    if (userId) {
        onlineUsers.set(userId, { socketId: socket.id, userName, role, groupCode, status: 'online', lastUpdate: new Date() });
        io.emit('online_students', Array.from(onlineUsers.values()));
    }

    socket.on('test_started', (data) => {
        if (onlineUsers.has(data.studentId)) {
            onlineUsers.get(data.studentId).status = 'testing';
            onlineUsers.get(data.studentId).currentTest = data.testTitle;
            io.emit('student_status_update', onlineUsers.get(data.studentId));
        }
    });

    socket.on('screen_update', (data) => {
        // Broadcast to admins
        socket.broadcast.emit('screen_mirror_update', data);
    });

    socket.on('test_progress', (data) => {
        if (onlineUsers.has(data.studentId)) {
            onlineUsers.get(data.studentId).progress = data.progress;
            io.emit('student_status_update', onlineUsers.get(data.studentId));
        }
    });

    socket.on('disconnect', () => {
        if (userId) {
            onlineUsers.delete(userId);
            io.emit('online_students', Array.from(onlineUsers.values()));
        }
    });
});

server.listen(PORT, () => console.log(`🚀 Server running on port ${PORT}`));
