# Contributing to Trading Signal Terminal

Thank you for your interest in contributing! 🎉

## Code of Conduct

Be respectful, inclusive, and helpful. We're all here to build something great together.

---

## How to Contribute

### 1. **Report Issues**
- Found a bug? [Open an issue](https://github.com/irFaN-dev30/qx/issues/new)
- Include:
  - Clear title & description
  - Steps to reproduce
  - Expected vs. actual behavior
  - Screenshots/logs if applicable

### 2. **Suggest Features**
- Have an idea? [Start a discussion](https://github.com/irFaN-dev30/qx/discussions)
- Explain the use case & benefits
- Provide examples if possible

### 3. **Submit Code**

#### Fork & Clone
```bash
git clone https://github.com/YOUR_USERNAME/qx
cd qx
git checkout -b feature/your-feature-name
```

#### Install Dependencies
```bash
# Python
pip install -r requirements.txt
pip install -r functions/signal_function/requirements.txt

# Frontend
cd dashboard
npm install
cd ..

# Playwright
python -m playwright install chromium
```

#### Make Your Changes

**Python Code Style:**
- Follow PEP 8
- Use type hints where possible
- Add docstrings to functions
- Format with `black`:
  ```bash
  black functions/signal_function/main.py
  ```

**JavaScript/React Code Style:**
- Use ES6+ syntax
- Follow ESLint rules (configured in `dashboard/`)
- Format with Prettier:
  ```bash
  cd dashboard && npm run lint
  ```

#### Testing (Local)

```bash
# Set environment variables
export QUOTEX_EMAIL="test@example.com"
export QUOTEX_PASSWORD="test_password"

# Test Python API
cd functions/signal_function
python -m pytest

# Test Frontend
cd dashboard
npm test
```

#### Commit & Push

```bash
git add .
git commit -m "feat: describe your changes clearly"
git push origin feature/your-feature-name
```

**Commit Message Format:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `style:` Code style (no logic change)
- `refactor:` Refactoring
- `perf:` Performance improvement
- `test:` Adding tests
- `chore:` Build/config changes

Example: `feat: add MACD indicator to signal generation`

#### Open a Pull Request

1. Go to [GitHub](https://github.com/irFaN-dev30/qx)
2. Click **"New Pull Request"**
3. Select your branch
4. Fill in the PR template:
   - **What:** What changes did you make?
   - **Why:** Why are these changes needed?
   - **How:** How do the changes work?
   - **Testing:** How did you test this?

---

## Project Structure

```
qx/
├── functions/signal_function/main.py    # Backend API logic
├── dashboard/app/page.js                 # Frontend UI
├── API-Quotex-main/                      # Quotex client library
├── requirements.txt                      # Python dependencies
└── README.md                             # Project documentation
```

---

## Areas We Need Help With

- 🐛 **Bug Fixes**: Check [open issues](https://github.com/irFaN-dev30/qx/issues)
- 📊 **New Indicators**: MACD, Stochastic, RSI divergence, etc.
- 🎨 **UI Improvements**: Dashboard design, responsive mobile view
- 📖 **Documentation**: Examples, tutorials, API docs
- 🧪 **Tests**: Unit & integration tests
- 🚀 **Performance**: Optimization & caching

---

## Development Tips

### Quick Local Setup
```bash
# One-liner setup
git clone https://github.com/YOUR_USERNAME/qx && cd qx && pip install -r requirements.txt && cd dashboard && npm install && cd ..
```

### Run Locally
```bash
# Terminal 1: Frontend
cd dashboard && npm run dev

# Terminal 2: Backend (optional, for testing)
export QUOTEX_EMAIL="your_email"
export QUOTEX_PASSWORD="your_password"
cd functions/signal_function && python -m flask run
```

### Debug Tips
- Check Vercel logs: `vercel logs`
- Python debug: Enable logging in `main.py`
- Network: Use browser DevTools (F12)
- Errors: Check `log-*.txt` files

---

## Questions?

- 📧 Email: irfan.dev30@gmail.com
- 💬 Telegram: [@irFaN_dev30](https://t.me/irFaN_dev30)
- 💡 GitHub Discussions: [Ask here](https://github.com/irFaN-dev30/qx/discussions)

---

## Recognition

Contributors are recognized in:
- Git commit history
- README.md "Acknowledgments" section
- Release notes

---

**Happy coding! 🚀**
