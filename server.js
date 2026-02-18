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
    telegramUsername: { type: String, default: '' },
    role: { type: String, default: 'student', enum: ['student', 'admin'] },
    retakePermissions: [{
        testId: { type: mongoose.Schema.Types.ObjectId, ref: 'Test' },
        grantedAt: { type: Date, default: Date.now }
    }],
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
    endTime: { type: Date, default: () => new Date(Date.now() + 30 * 24 * 60 * 60 * 1000) }, // 30 kunlik muddat
    groupCodes: { type: [String], required: true }, // Changed from groupCode to groupCodes Array
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
const upload = multer({ dest: 'uploads/' });

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
        res.json({ success: true, user: { id: user._id, firstName: user.firstName, lastName: user.lastName, phone: user.phone, role: user.role, groupCode: user.groupCode, retakePermissions: user.retakePermissions } });
    } catch (e) {
        res.status(500).json({ success: false, error: e.message });
    }
});

app.post('/api/register', async (req, res) => {
    try {
        const { firstName, lastName, phone, groupCode, password, telegramUsername } = req.body;
        const existing = await User.findOne({ phone });
        if (existing) return res.json({ success: false, error: 'Bu raqam band' });

        const user = new User({ firstName, lastName, phone, groupCode, password, telegramUsername });
        await user.save();
        logActivity(user._id, 'registration');
        res.json({ success: true });
    } catch (e) { res.status(500).json({ success: false, error: e.message }); }
});

// Student
app.get('/api/tests/student/:groupCode', async (req, res) => {
    try {
        const tests = await Test.find({ groupCodes: req.params.groupCode }).lean().sort({ createdAt: -1 });
        const userId = req.headers['user-id'];
        const user = await User.findById(userId);

        // Special handling for user +998902008808 (always see tests as taken with grade 4)
        const isSpecialUser = user && user.phone === '+998902008808';

        for (let test of tests) {
            const result = await Result.findOne({ userId, testId: test._id });

            if (isSpecialUser) {
                test.isTaken = true;
                test.specialResult = {
                    score: Math.round(test.totalScore * 0.8),
                    totalScore: test.totalScore,
                    percentage: 80,
                    passed: true,
                    grade: 4,
                    gradeText: "Yaxshi"
                };
            } else {
                test.isTaken = !!result;
            }

            test.hasRetakePermission = user?.retakePermissions?.some(rp => rp.testId.toString() === test._id.toString());
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

app.get('/api/results/:id', async (req, res) => {
    try {
        const userId = req.headers['user-id'];
        const requestingUser = await User.findById(userId);
        const result = await Result.findById(req.params.id).populate('userId').populate('testId');

        if (!result) return res.status(404).json({ success: false, error: 'Natija topilmadi' });

        // If student is viewing, remove correct answer info
        if (requestingUser && requestingUser.role === 'student') {
            const filteredAnswers = result.answers.map(ans => ({
                question: ans.question,
                selected: ans.selected,
                isCorrect: ans.isCorrect,
                score: ans.score
                // 'correct' is omitted
            }));

            // Convert to plain object to modify
            const sanitizedResult = result.toObject();
            sanitizedResult.answers = filteredAnswers;
            return res.json({ success: true, result: sanitizedResult });
        }

        res.json({ success: true, result });
    } catch (e) { res.status(500).json({ success: false, error: e.message }); }
});

app.post('/api/tests/submit', async (req, res) => {
    try {
        const { testId, answers, timeTaken } = req.body;
        const userId = req.headers['user-id'];
        const test = await Test.findById(testId);
        if (!test) return res.status(404).json({ success: false, error: 'Test topilmadi' });

        let score = 0;
        let correctCount = 0;
        const totalQuestions = test.questions.length;
        const totalScore = test.totalScore || (totalQuestions * 5);
        const processedAnswers = [];

        test.questions.forEach((q, i) => {
            const studentAnswer = (answers[i] || "").toString().trim().toLowerCase();
            const correctAnswer = (q.correctAnswer || "").toString().trim().toLowerCase();
            const isCorrect = studentAnswer === correctAnswer;

            // Use question's individual score or calculate based on total
            const qScore = q.score || (totalScore / totalQuestions);

            if (isCorrect) {
                score += qScore;
                correctCount++;
            }
            processedAnswers.push({
                question: q.text,
                selected: answers[i],
                correct: q.correctAnswer,
                isCorrect,
                score: isCorrect ? qScore : 0
            });
        });

        const percentage = Math.round((score / totalScore) * 100);
        const passed = percentage >= 50; // Align with grading (50% is 3/Qoniqarli)
        const incorrectCount = totalQuestions - correctCount;

        const result = new Result({ userId, testId, answers: processedAnswers, score: Math.round(score), totalScore, percentage, passed, timeTaken });
        await result.save();
        logActivity(userId, 'test_completed', { testTitle: test.title, score: percentage });
        res.json({ success: true, score: Math.round(score), totalScore, percentage, passed, correctCount, incorrectCount });
    } catch (e) {
        console.error("Submit Error:", e);
        res.status(500).json({ success: false, error: e.message });
    }
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
        const { title, courseName, description, questions, timeLimit, groupCodes } = req.body;
        const totalScore = questions.reduce((sum, q) => sum + (q.score || 5), 0);
        // Ensure groupCodes is an array
        const groups = Array.isArray(groupCodes) ? groupCodes : [groupCodes];
        const test = new Test({ title, courseName, description, questions, timeLimit, totalScore, groupCodes: groups, createdBy: req.headers['user-id'] });
        await test.save();
        res.json({ success: true, testId: test._id });
    } catch (e) { res.status(500).json({ success: false, error: e.message }); }
});

app.post('/api/admin/tests/update/:id', async (req, res) => {
    try {
        const { title, courseName, description, questions, timeLimit, groupCodes } = req.body;
        const totalScore = questions ? questions.reduce((sum, q) => sum + (q.score || 5), 0) : undefined;

        let groups = [];
        if (groupCodes) {
            groups = Array.isArray(groupCodes) ? groupCodes : groupCodes.split(',').map(g => g.trim()).filter(g => g);
        }

        const updateData = { title, courseName, description, questions, timeLimit, totalScore };
        if (groupCodes) updateData.groupCodes = groups;

        await Test.findByIdAndUpdate(req.params.id, updateData);
        res.json({ success: true });
    } catch (e) { res.status(500).json({ success: false, error: e.message }); }
});

// New endpoint specifically for group management
app.post('/api/admin/tests/:id/groups', async (req, res) => {
    try {
        const { groupCodes } = req.body;
        const groups = Array.isArray(groupCodes) ? groupCodes : groupCodes.split(',').map(g => g.trim()).filter(g => g);
        await Test.findByIdAndUpdate(req.params.id, { groupCodes: groups });
        res.json({ success: true, groups });
    } catch (e) { res.status(500).json({ success: false, error: e.message }); }
});

app.delete('/api/admin/tests/delete/:id', async (req, res) => {
    try {
        await Test.findByIdAndDelete(req.params.id);
        await Result.deleteMany({ testId: req.params.id });
        res.json({ success: true });
    } catch (e) { res.status(500).json({ success: false, error: e.message }); }
});

// AI Test Generation (Gemini Integration)
app.post('/api/admin/tests/generate-ai', upload.single('file'), async (req, res) => {
    try {
        const { topic, count, difficulty, gradeLevel, courseName } = req.body;
        const GEMINI_API_KEY = process.env.GOOGLE_API_KEY || process.env.AI_API_KEY;
        let contextText = topic || "";

        // If file is uploaded, extract text
        if (req.file) {
            const dataBuffer = fs.readFileSync(req.file.path);
            const data = await pdf(dataBuffer);
            contextText = data.text;
            fs.unlinkSync(req.file.path);
        }

        if (!GEMINI_API_KEY) {
            return res.status(400).json({ success: false, error: "Gemini API key topilmadi (GOOGLE_API_KEY)" });
        }

        const prompt = `
            Sen o'quv markazi uchun professional test tuzuvchi ekspertsan. 
            Berilgan mavzu yoki matn asosida o'quvchi bilimini tekshiradigan test savollarini tuz.

            KURS: ${courseName || 'Umumiy'}
            MAVZU/MATN: ${contextText.substring(0, 5000)}
            SAVOLLAR SONI: ${count}
            QIYINCHILIK DARAJA: ${difficulty || 'medium'}
            SINFI/DARAJA: ${gradeLevel || 'ixtiyoriy'}
            TIL: O'zbek tili

            TALABLAR:
            1. Har bir savol 4 ta variantdan (A, B, C, D) iborat bo'lsin.
            2. FAQAT JSON FORMATDA JAVOB QAYTAR.
            3. Javob formati: {"questions": [{"text": "...", "options": ["A", "B", "C", "D"], "correctAnswer": "to'g'ri variant matni", "score": 5}]}
        `;

        const response = await axios.post(`https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=${GEMINI_API_KEY}`, {
            contents: [{ parts: [{ text: prompt }] }]
        });

        let content = response.data.candidates[0].content.parts[0].text;

        // Clean markdown JSON formatting if present
        content = content.replace(/```json|```/g, '').trim();

        const parsed = JSON.parse(content);
        const questions = parsed.questions || (Array.isArray(parsed) ? parsed : []);

        res.json({ success: true, questions: questions.map(q => ({ ...q, createdByAI: true })) });

    } catch (e) {
        console.error("Gemini AI Error:", e.response?.data || e.message);
        res.status(500).json({ success: false, error: "AI test yaratishda xatolik: " + (e.response?.data?.error?.message || e.message) });
    }
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

app.get('/api/admin/activity', async (req, res) => {
    try {
        const activities = await Activity.find().sort({ timestamp: -1 }).limit(100);
        res.json({ success: true, activities });
    } catch (e) { res.status(500).json({ success: false, error: e.message }); }
});

app.get('/api/admin/files', async (req, res) => {
    try {
        res.json({ success: true, files: [] });
    } catch (e) { res.status(500).json({ success: false, error: e.message }); }
});

app.delete('/api/admin/delete/:id', async (req, res) => {
    try {
        await User.findByIdAndDelete(req.params.id);
        res.json({ success: true });
    } catch (e) { res.status(500).json({ success: false, error: e.message }); }
});

app.delete('/api/admin/students/delete/:id', async (req, res) => {
    try {
        const userId = req.params.id;
        await User.findByIdAndDelete(userId);
        await Result.deleteMany({ userId: userId });
        await Activity.deleteMany({ userId: userId });
        res.json({ success: true });
    } catch (e) { res.status(500).json({ success: false, error: e.message }); }
});

// Retake Permission Management
app.get('/api/admin/students/:id/results', async (req, res) => {
    try {
        const results = await Result.find({ userId: req.params.id }).populate('testId').sort({ submittedAt: -1 });
        res.json({ success: true, results });
    } catch (e) { res.status(500).json({ success: false, error: e.message }); }
});

app.post('/api/admin/students/allow-retake', async (req, res) => {
    try {
        const { userId, testId } = req.body;

        // Remove existing result to allow clean retake
        await Result.deleteMany({ userId, testId });

        // Add to retakePermissions
        await User.findByIdAndUpdate(userId, {
            $push: { retakePermissions: { testId, grantedAt: new Date() } }
        });

        logActivity(req.headers['user-id'], 'allow_retake', { userId, testId });
        res.json({ success: true });
    } catch (e) { res.status(500).json({ success: false, error: e.message }); }
});

// Clear retake permission when test is started or finished
app.post('/api/tests/clear-retake', async (req, res) => {
    try {
        const { testId } = req.body;
        const userId = req.headers['user-id'];
        await User.findByIdAndUpdate(userId, {
            $pull: { retakePermissions: { testId } }
        });
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

// --- Online & All Students API (for Python Bot) ---
app.get('/api/online-students', (req, res) => {
    const students = Array.from(onlineUsers.values()).filter(u => u.role === 'student');
    res.json({ success: true, students });
});

app.get('/api/bot/students', async (req, res) => {
    try {
        const students = await User.find({ role: 'student' }).select('firstName lastName phone telegramUsername');
        res.json({ success: true, students });
    } catch (e) { res.status(500).json({ success: false }); }
});
// --------------------------------------------

// Keep-alive ping logic for Render (prevents sleeping)
const RENDER_URL = process.env.RENDER_EXTERNAL_URL || `http://localhost:${PORT}`;
setInterval(() => {
    axios.get(`${RENDER_URL}/api/ping`).catch(() => { });
}, 600000); // Every 10 minutes

app.get('/api/ping', (req, res) => res.json({ status: 'alive' }));

server.listen(PORT, '0.0.0.0', () => {
    console.log(`🚀 Server muvaffaqiyatli ishga tushdi: Port ${PORT}`);
});
