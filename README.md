# Wedding Voice Samples Collection Bot

<div align="center">
  <img src="https://img.shields.io/badge/python-3.x-blue.svg" alt="Python 3.x">
  <img src="https://img.shields.io/badge/telegram-bot-blue.svg" alt="Telegram Bot">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License: MIT">
</div>

## 📝 Overview

This project features a custom Telegram bot designed for collecting voice recordings from friends for a surprise trance music track for Eran and Adi's wedding. The bot guides users through the process of recording audio samples in specific categories, which are then processed into a cohesive music track.

## 🔥 Key Features

- **Interactive Telegram Bot**: User-friendly interface for collecting voice recordings
- **Categorical Recording**: Structured categories for different types of voice samples
- **Personalized User Directories**: Each contributor's recordings are organized in their own directory
- **Automatic Audio Processing**: OGG to MP3 conversion for compatibility with music production software
- **Real-time Feedback**: Instant confirmation when recordings are successfully saved
- **Multi-language Support**: Interface in Hebrew with support for international users

## 🎵 Recording Categories

The bot currently supports two main categories:

1. **Pre-Drop Excitement**: Short, energetic clips to build up the energy before the drop in the track
   - Examples: "Let's go Eran!", "Here it comes!", excited shouts, etc.
   - Recommended length: 2-5 seconds

2. **General Ideas**: Any creative content that doesn't fit the other category
   - Examples: "Congratulations!", "We love you!", or any other audio clip
   - Flexible length

## 🛠️ Technical Architecture

### Components
- **Telegram Bot (Python)**: Frontend interface for users to interact with
- **File Storage System**: Organized directory structure for recordings
- **Conversion Script**: Separate utility for OGG to MP3 conversion using ffmpeg
- **Tracking System**: Logs file conversion history to process only new files

### Directory Structure
```
eran_wedding_bot/
├── bot.py                # Main bot implementation
├── convert_to_mp3.py     # Audio conversion script
├── run_conversion.sh     # Shell script to run the conversion
├── media/                # Media files used by the bot
├── recordings/           # OGG recordings from users
│   ├── [User1]/          # Individual user directories
│   ├── [User2]/
│   └── ...
└── mp3_recordings/       # Converted MP3 files
    ├── [User1]/
    ├── [User2]/
    └── ...
```

## 🚀 Installation

### Prerequisites
- Python 3.x
- Telegram Bot API token
- ffmpeg installed on your system

### Setup
1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/wedding-voice-bot.git
   cd wedding-voice-bot
   ```

2. Install required dependencies:
   ```bash
   pip install python-telegram-bot pydub
   ```

3. Install ffmpeg (if not already installed):
   - **macOS**:
     ```bash
     brew install ffmpeg
     ```
   - **Ubuntu/Debian**:
     ```bash
     sudo apt-get install ffmpeg
     ```
   - **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html)

4. Create a Telegram bot using [BotFather](https://t.me/botfather) and get your token

5. Update the token in `eran_wedding_bot/bot.py`:
   ```python
   BOT_TOKEN = "YOUR_TOKEN_HERE"
   ```

## 🎮 Usage

### Starting the Bot
Run the bot with:
```bash
python3 eran_wedding_bot/bot.py
```

### User Interaction
1. Users find the bot on Telegram
2. Send `/start` to begin
3. Enter their name (English characters only)
4. Navigate through categories and record voice messages
5. Submit at least 2-3 recordings per category

### Converting Recordings
To convert new OGG files to MP3:
```bash
./eran_wedding_bot/run_conversion.sh
```

## 📊 Project Status

This project was created specifically for Eran and Adi's wedding. It's feature-complete for its intended purpose but can be adapted for similar events.

## 🔒 Privacy Considerations

- All recordings are stored locally, not on public servers
- User data (names) are used only for file organization
- No personal data is shared with third parties

## 🤝 Contributing

Although this was a personal project, contributions are welcome:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📧 Contact

Project created by Tsach - Feel free to reach out with questions!

---

<div align="center">
  <strong>Made with ❤️ for Eran and Adi's special day</strong>
</div> 