<template>
  <div class="chat-wrapper">
    <!-- Modern Header -->
    <header class="chat-header">
      <div class="header-content">
        <div class="logo-section">
          <div class="logo-icon">
            <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="16" cy="16" r="14" stroke="currentColor" stroke-width="2"/>
              <path d="M16 8v8m0 0l-4-4m4 4l4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              <circle cx="16" cy="20" r="2" fill="currentColor"/>
            </svg>
          </div>
          <div class="logo-text">
            <h1>Clinical Assistant</h1>
            <p class="tagline">Your AI-powered medical reference</p>
          </div>
        </div>
        <div class="header-actions">
          <button class="icon-button" @click="toggleTheme" :title="isDarkMode ? 'Light mode' : 'Dark mode'">
            <svg v-if="!isDarkMode" width="20" height="20" viewBox="0 0 20 20" fill="none">
              <circle cx="10" cy="10" r="4" stroke="currentColor" stroke-width="2"/>
              <path d="M10 1v2m0 14v2m9-9h-2M3 10H1m15.364-6.364l-1.414 1.414M5.05 14.95l-1.414 1.414m12.728 0l-1.414-1.414M5.05 5.05L3.636 3.636" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
            <svg v-else width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M10 3a7 7 0 100 14 7 7 0 000-14z" fill="currentColor"/>
              <path d="M10 1a9 9 0 01.832 17.98A7 7 0 1110 1z" fill="currentColor" opacity="0.4"/>
            </svg>
          </button>
          <button class="icon-button" @click="clearChat" title="New chat">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M5 2h10a2 2 0 012 2v12a2 2 0 01-2 2H5a2 2 0 01-2-2V4a2 2 0 012-2z" stroke="currentColor" stroke-width="2"/>
              <path d="M10 6v8m-4-4h8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </button>
        </div>
      </div>
    </header>

    <!-- Modern Chat Container -->
    <main class="chat-container">
      <div class="messages-area" ref="messagesContainer">
        <div class="messages-inner">
          <!-- Welcome Message -->
          <div v-if="messages.length === 1" class="welcome-screen">
            <div class="welcome-content">
              <div class="welcome-icon">
                <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
                  <circle cx="32" cy="32" r="28" stroke="currentColor" stroke-width="2" opacity="0.2"/>
                  <path d="M32 16v16m0 0l-8-8m8 8l8-8" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>
                  <circle cx="32" cy="40" r="4" fill="currentColor"/>
                </svg>
              </div>
              <h2>Welcome to Clinical Assistant</h2>
              <p>I can help you with questions about clinical procedures, medical techniques, and best practices from the clinical skills handbook.</p>
              <div class="suggested-prompts">
                <button 
                  v-for="prompt in suggestedPrompts" 
                  :key="prompt"
                  @click="sendSuggestedPrompt(prompt)"
                  class="prompt-chip"
                >
                  {{ prompt }}
                </button>
              </div>
            </div>
          </div>

          <!-- Messages -->
          <div v-for="message in messages" :key="message.id" class="message-wrapper" :class="message.sender">
            <div class="message-content-wrapper">
              <div v-if="message.sender === 'bot'" class="avatar">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                  <circle cx="12" cy="12" r="10" fill="currentColor" opacity="0.1"/>
                  <path d="M12 6v6l-3-3m3 3l3-3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                  <circle cx="12" cy="15" r="1.5" fill="currentColor"/>
                </svg>
              </div>
              
              <div class="message-bubble">
                <div class="message-text" v-html="formatMessage(message.content)"></div>
                
                <!-- Modern Image Gallery for Extracted Content -->
                <div v-if="message.images && message.images.length > 0" class="image-gallery extracted-images">
                  <h4 class="gallery-title">Relevant Diagrams & Tables</h4>
                  <div class="image-grid">
                    <div 
                      v-for="(image, index) in message.images" 
                      :key="index" 
                      class="image-card"
                      @click="showFullImage(image.url)"
                    >
                      <img :src="image.url" :alt="image.caption">
                      <div class="image-overlay">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                          <path d="M15 3h6v6m-6 0l6-6M9 21H3v-6m6 0l-6 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                      </div>
                      <div class="image-caption">{{ image.caption }}</div>
                    </div>
                  </div>
                </div>
                
                <!-- Full Page Images Section -->
                <div v-if="message.pageImages && message.pageImages.length > 0" class="page-images-section">
                  <h4 class="gallery-title">Full Page References</h4>
                  <div class="page-images-grid">
                    <div 
                      v-for="(pageImg, index) in message.pageImages" 
                      :key="`page-${index}`" 
                      class="page-image-card"
                      @click="showFullImage(pageImg.url)"
                    >
                      <div class="page-preview">
                        <img :src="pageImg.url" :alt="pageImg.caption">
                        <div class="page-overlay">
                          <div class="page-number">{{ pageImg.caption }}</div>
                          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" class="expand-icon">
                            <path d="M15 3h6v6m-6 0l6-6M9 21H3v-6m6 0l-6 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                          </svg>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Modern Loading State -->
          <div v-if="isLoading" class="message-wrapper bot">
            <div class="message-content-wrapper">
              <div class="avatar">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                  <circle cx="12" cy="12" r="10" fill="currentColor" opacity="0.1"/>
                  <path d="M12 6v6l-3-3m3 3l3-3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                  <circle cx="12" cy="15" r="1.5" fill="currentColor"/>
                </svg>
              </div>
              <div class="message-bubble thinking">
                <div class="thinking-dots">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Modern Input Area -->
      <div class="input-area">
        <div class="input-wrapper">
          <textarea
            v-model="inputMessage"
            @keydown.enter.prevent="handleEnterKey"
            placeholder="Ask about clinical procedures, techniques, or best practices..."
            :disabled="isLoading"
            class="message-input"
            rows="1"
            ref="messageInput"
          ></textarea>
          <button 
            @click="sendMessage" 
            :disabled="isLoading || !inputMessage.trim()" 
            class="send-button"
            :class="{ 'active': inputMessage.trim() }"
          >
            <svg v-if="!isLoading" width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M2 10l15-7.5v15L2 10zm15 0H8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <svg v-else width="20" height="20" viewBox="0 0 20 20" fill="none" class="spinner">
              <circle cx="10" cy="10" r="8" stroke="currentColor" stroke-width="2" fill="none" stroke-dasharray="50.265" stroke-dashoffset="12.566" stroke-linecap="round"/>
            </svg>
          </button>
        </div>
        <div class="input-footer">
          <span class="footer-text">AI can make mistakes. Verify important information.</span>
        </div>
      </div>
    </main>

    <!-- Modern Full Image Modal -->
    <Transition name="modal">
      <div v-if="fullImageUrl" class="image-modal" @click="fullImageUrl = null">
        <div class="modal-content" @click.stop>
          <button class="modal-close" @click="fullImageUrl = null">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
              <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </button>
          <img :src="fullImageUrl" alt="Full size image">
        </div>
      </div>
    </Transition>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      messages: [],
      inputMessage: '',
      isLoading: false,
      messageIdCounter: 1,
      chatHistory: [],
      fullImageUrl: null,
      isDarkMode: false,
      suggestedPrompts: [
        "How do I measure blood pressure correctly?",
        "What's the proper technique for giving injections?",
        "Explain sterile field preparation",
        "Best practices for patient positioning"
      ]
    };
  },
  mounted() {
    // Initialize with welcome message
    this.messages = [{
      id: 0,
      content: 'Hello! I\'m your clinical skills assistant. How can I help you today?',
      sender: 'bot',
      time: this.formatTime(new Date()),
      images: []
    }];
    
    // Check for dark mode preference
    this.isDarkMode = localStorage.getItem('darkMode') === 'true' || 
                     window.matchMedia('(prefers-color-scheme: dark)').matches;
    this.applyTheme();
    
    // Auto-resize textarea
    this.$nextTick(() => {
      this.adjustTextareaHeight();
    });
  },
  methods: {
    async sendMessage() {
      if (!this.inputMessage.trim() || this.isLoading) return;
      
      const userMessage = this.inputMessage.trim();
      this.inputMessage = '';
      this.adjustTextareaHeight();
      
      // Add user message
      this.messages.push({
        id: this.messageIdCounter++,
        content: userMessage,
        sender: 'user',
        time: this.formatTime(new Date()),
        images: []
      });
      
      this.chatHistory.push({ role: 'user', content: userMessage });
      this.isLoading = true;
      this.scrollToBottom();
      
      try {
        const response = await axios.post('http://127.0.0.1:8000/api/query', {
          query: userMessage,
          chat_history: this.chatHistory
        });
        
        const { text_response, citations } = response.data;
        
        this.chatHistory.push({ role: 'assistant', content: text_response });
        
        // Process images from citations
        const extractedImages = [];
        const pageImages = [];
        
        if (citations) {
          citations.forEach(citation => {
            if (citation.content_type === 'full_page') {
              pageImages.push({
                url: citation.image_url,
                caption: citation.caption || `Page ${citation.source_page}`,
                page: citation.source_page
              });
            } else {
              extractedImages.push({
                url: citation.image_url,
                caption: `Page ${citation.source_page} - ${citation.content_type}`,
                page: citation.source_page
              });
            }
          });
        }
        
        // Add bot response to chat
        this.messages.push({
          id: this.messageIdCounter++,
          content: text_response,
          sender: 'bot',
          time: this.formatTime(new Date()),
          images: extractedImages,
          pageImages: pageImages
        });
        
      } catch (error) {
        console.error('Error:', error);
        this.messages.push({
          id: this.messageIdCounter++,
          content: 'I apologize, but I encountered an error. Please ensure the backend server is running and try again.',
          sender: 'bot',
          time: this.formatTime(new Date()),
          images: []
        });
      } finally {
        this.isLoading = false;
        this.scrollToBottom();
      }
    },
    
    sendSuggestedPrompt(prompt) {
      this.inputMessage = prompt;
      this.sendMessage();
    },
    
    handleEnterKey(event) {
      if (!event.shiftKey) {
        this.sendMessage();
      } else {
        // Allow shift+enter for new lines
        this.$nextTick(() => this.adjustTextareaHeight());
      }
    },
    
    adjustTextareaHeight() {
      const textarea = this.$refs.messageInput;
      if (textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
      }
    },
    
    formatMessage(content) {
      // Convert markdown-style formatting to HTML
      return content
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`(.*?)`/g, '<code>$1</code>')
        .replace(/\n/g, '<br>');
    },
    
    formatTime(date) {
      return date.toLocaleTimeString('en-US', { 
        hour: 'numeric', 
        minute: '2-digit',
        hour12: true 
      });
    },
    
    scrollToBottom() {
      this.$nextTick(() => {
        const container = this.$refs.messagesContainer;
        if (container) {
          container.scrollTo({
            top: container.scrollHeight,
            behavior: 'smooth'
          });
        }
      });
    },
    
    showFullImage(url) {
      this.fullImageUrl = url;
    },
    
    toggleTheme() {
      this.isDarkMode = !this.isDarkMode;
      localStorage.setItem('darkMode', this.isDarkMode);
      this.applyTheme();
    },
    
    applyTheme() {
      document.documentElement.setAttribute('data-theme', this.isDarkMode ? 'dark' : 'light');
    },
    
    clearChat() {
      if (this.messages.length > 1 && confirm('Start a new conversation?')) {
        this.messages = [{
          id: 0,
          content: 'Hello! I\'m your clinical skills assistant. How can I help you today?',
          sender: 'bot',
          time: this.formatTime(new Date()),
          images: []
        }];
        this.chatHistory = [];
        this.messageIdCounter = 1;
      }
    }
  },
  watch: {
    inputMessage() {
      this.$nextTick(() => this.adjustTextareaHeight());
    }
  }
};
</script>

<style>
/* CSS Variables for theming */
:root {
  /* Light theme */
  --bg-primary: #ffffff;
  --bg-secondary: #f7f8fa;
  --bg-tertiary: #eef0f3;
  --text-primary: #1a1a1a;
  --text-secondary: #5f6368;
  --text-tertiary: #9aa0a6;
  --border-color: #e8eaed;
  --accent-color: #1a73e8;
  --accent-hover: #1557b0;
  --user-bubble: #1a73e8;
  --bot-bubble: #f1f3f4;
  --bot-text: #202124;
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.07);
  --shadow-lg: 0 10px 25px rgba(0, 0, 0, 0.1);
}

[data-theme="dark"] {
  --bg-primary: #1e1e1e;
  --bg-secondary: #2d2d2d;
  --bg-tertiary: #3c3c3c;
  --text-primary: #e8eaed;
  --text-secondary: #9aa0a6;
  --text-tertiary: #80868b;
  --border-color: #3c4043;
  --accent-color: #8ab4f8;
  --accent-hover: #aecbfa;
  --user-bubble: #1a73e8;
  --bot-bubble: #3c4043;
  --bot-text: #e8eaed;
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.2);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.3);
  --shadow-lg: 0 10px 25px rgba(0, 0, 0, 0.4);
}

/* Global styles */
* {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* Main layout */
.chat-wrapper {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--bg-primary);
  color: var(--text-primary);
  transition: background-color 0.3s ease;
}

/* Header styles */
.chat-header {
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border-color);
  padding: 0.75rem 0;
  position: sticky;
  top: 0;
  z-index: 100;
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  background: rgba(255, 255, 255, 0.85);
}

[data-theme="dark"] .chat-header {
  background: rgba(30, 30, 30, 0.85);
}

.header-content {
  max-width: 1000px;
  margin: 0 auto;
  padding: 0 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo-section {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.logo-icon {
  color: var(--accent-color);
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-3px); }
}

.logo-text h1 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  letter-spacing: -0.02em;
}

.tagline {
  margin: 0;
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.header-actions {
  display: flex;
  gap: 0.5rem;
}

.icon-button {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 8px;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.icon-button:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
  transform: translateY(-1px);
}

/* Chat container */
.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--bg-secondary);
}

/* Messages area */
.messages-area {
  flex: 1;
  overflow-y: auto;
  scroll-behavior: smooth;
  padding: 2rem 0;
}

.messages-area::-webkit-scrollbar {
  width: 6px;
}

.messages-area::-webkit-scrollbar-track {
  background: transparent;
}

.messages-area::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 3px;
}

.messages-area::-webkit-scrollbar-thumb:hover {
  background: var(--text-tertiary);
}

.messages-inner {
  max-width: 800px;
  margin: 0 auto;
  padding: 0 1.5rem;
}

/* Welcome screen */
.welcome-screen {
  text-align: center;
  padding: 3rem 0;
  animation: fadeIn 0.5s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.welcome-content {
  max-width: 600px;
  margin: 0 auto;
}

.welcome-icon {
  color: var(--accent-color);
  margin-bottom: 2rem;
  opacity: 0.8;
}

.welcome-content h2 {
  font-size: 1.75rem;
  font-weight: 600;
  margin: 0 0 1rem;
  letter-spacing: -0.02em;
}

.welcome-content p {
  font-size: 1rem;
  color: var(--text-secondary);
  margin: 0 0 2rem;
  line-height: 1.6;
}

.suggested-prompts {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  justify-content: center;
}

.prompt-chip {
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 20px;
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
  color: var(--text-primary);
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.prompt-chip:hover {
  background: var(--accent-color);
  color: white;
  border-color: var(--accent-color);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

/* Message styles */
.message-wrapper {
  margin-bottom: 1.5rem;
  animation: messageSlideIn 0.3s ease;
}

@keyframes messageSlideIn {
  from { 
    opacity: 0; 
    transform: translateY(10px); 
  }
  to { 
    opacity: 1; 
    transform: translateY(0); 
  }
}

.message-wrapper.user {
  text-align: right;
}

.message-content-wrapper {
  display: inline-flex;
  align-items: flex-end;
  gap: 0.5rem;
  max-width: 100%;
}

.message-wrapper.user .message-content-wrapper {
  flex-direction: row-reverse;
}

.avatar {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: var(--bg-tertiary);
  color: var(--accent-color);
}

.message-bubble {
  background: var(--bot-bubble);
  color: var(--bot-text);
  border-radius: 18px;
  padding: 0.75rem 1rem;
  max-width: 500px;
  word-wrap: break-word;
  box-shadow: var(--shadow-sm);
  position: relative;
}

.message-wrapper.user .message-bubble {
  background: var(--user-bubble);
  color: white;
  border-bottom-right-radius: 4px;
}

.message-wrapper.bot .message-bubble {
  border-bottom-left-radius: 4px;
}

.message-text {
  font-size: 0.9375rem;
  line-height: 1.5;
}

.message-text strong {
  font-weight: 600;
}

.message-text code {
  background: rgba(0, 0, 0, 0.06);
  padding: 0.125rem 0.375rem;
  border-radius: 4px;
  font-family: 'SF Mono', Consolas, monospace;
  font-size: 0.875em;
}

[data-theme="dark"] .message-text code {
  background: rgba(255, 255, 255, 0.1);
}

/* Thinking animation */
.message-bubble.thinking {
  padding: 1rem 1.5rem;
}

.thinking-dots {
  display: flex;
  gap: 0.25rem;
}

.thinking-dots span {
  width: 8px;
  height: 8px;
  background: var(--text-tertiary);
  border-radius: 50%;
  animation: bounce 1.4s ease-in-out infinite;
}

.thinking-dots span:nth-child(1) { animation-delay: -0.32s; }
.thinking-dots span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { 
    transform: scale(0.8);
    opacity: 0.5;
  }
  40% { 
    transform: scale(1);
    opacity: 1;
  }
}

/* Image gallery */
.image-gallery {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
}

.image-card {
  position: relative;
  border-radius: 0.75rem;
  overflow: hidden;
  cursor: pointer;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  transition: all 0.3s ease;
}

.image-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
  border-color: var(--accent-color);
}

.image-card img {
  width: 100%;
  height: 150px;
  object-fit: cover;
  display: block;
}

.image-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s ease;
  color: white;
}

.image-card:hover .image-overlay {
  opacity: 1;
}

.image-caption {
  padding: 0.75rem;
  font-size: 0.875rem;
  color: var(--text-secondary);
  background: var(--bg-primary);
}

/* Input area */
.input-area {
  background: var(--bg-primary);
  border-top: 1px solid var(--border-color);
  padding: 1rem 0;
}

.input-wrapper {
  max-width: 900px;
  margin: 0 auto;
  padding: 0 1rem;
  display: flex;
  gap: 0.75rem;
  align-items: flex-end;
}

.message-input {
  flex: 1;
  min-height: 44px;
  max-height: 200px;
  padding: 0.75rem 1.25rem;
  border: 1px solid var(--border-color);
  border-radius: 1.5rem;
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 1rem;
  font-family: inherit;
  resize: none;
  outline: none;
  transition: all 0.2s ease;
  line-height: 1.5;
}

.message-input:focus {
  border-color: var(--accent-color);
  background: var(--bg-primary);
}

.message-input::placeholder {
  color: var(--text-tertiary);
}

.send-button {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  border: none;
  background: var(--bg-tertiary);
  color: var(--text-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.send-button.active {
  background: var(--accent-color);
  color: white;
}

.send-button:hover:not(:disabled) {
  transform: scale(1.05);
}

.send-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.input-footer {
  text-align: center;
  padding: 0.5rem 1rem 0;
}

.footer-text {
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

/* Modal styles */
.image-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 2rem;
}

.modal-content {
  position: relative;
  max-width: 90vw;
  max-height: 90vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-content img {
  max-width: 100%;
  max-height: 90vh;
  object-fit: contain;
  border-radius: 0.5rem;
}

.modal-close {
  position: absolute;
  top: -3rem;
  right: 0;
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 50%;
  border: none;
  background: rgba(255, 255, 255, 0.1);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.modal-close:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: scale(1.1);
}

/* Modal transitions */
.modal-enter-active, .modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from, .modal-leave-to {
  opacity: 0;
}

/* Responsive design */
@media (max-width: 768px) {
  .header-content {
    padding: 0 1rem;
  }
  
  .logo-text h1 {
    font-size: 1.25rem;
  }
  
  .tagline {
    display: none;
  }
  
  .messages-inner {
    padding: 1rem 0.5rem;
  }
  
  .message-content-wrapper {
    max-width: 95%;
  }
  
  .welcome-screen {
    padding: 2rem 1rem;
  }
  
  .suggested-prompts {
    flex-direction: column;
  }
  
  .prompt-chip {
    width: 100%;
    text-align: center;
  }
}

/* Scrollbar styling */
.messages-area::-webkit-scrollbar {
  width: 8px;
}

.messages-area::-webkit-scrollbar-track {
  background: transparent;
}

.messages-area::-webkit-scrollbar-thumb {
  background: var(--text-tertiary);
  border-radius: 4px;
  opacity: 0.3;
}

.messages-area::-webkit-scrollbar-thumb:hover {
  background: var(--text-secondary);
  opacity: 0.5;
}

/* Print styles */
@media print {
  .chat-header,
  .input-area,
  .icon-button,
  .image-overlay {
    display: none;
  }
  
  .message-wrapper {
    break-inside: avoid;
  }
}

/* Image gallery improvements */
.gallery-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-secondary);
  margin: 1rem 0 0.5rem 0;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.extracted-images {
  margin-top: 1rem;
}

.image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 0.75rem;
}

/* Full page images section */
.page-images-section {
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border-color);
}

.page-images-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 1rem;
}

.page-image-card {
  position: relative;
  cursor: pointer;
  transition: all 0.3s ease;
}

.page-preview {
  position: relative;
  border-radius: 0.5rem;
  overflow: hidden;
  background: var(--bg-tertiary);
  border: 2px solid var(--border-color);
  aspect-ratio: 8.5 / 11; /* US Letter aspect ratio */
}

.page-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.page-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(to bottom, 
    rgba(0, 0, 0, 0.7) 0%, 
    rgba(0, 0, 0, 0.3) 20%,
    rgba(0, 0, 0, 0.1) 50%,
    rgba(0, 0, 0, 0.7) 100%
  );
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.page-image-card:hover .page-overlay {
  opacity: 1;
}

.page-image-card:hover {
  transform: translateY(-4px);
}

.page-image-card:hover .page-preview {
  border-color: var(--accent-color);
  box-shadow: var(--shadow-lg);
}

.page-number {
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 0.25rem 0.75rem;
  border-radius: 1rem;
  font-size: 0.875rem;
  font-weight: 600;
}

.expand-icon {
  color: white;
}

/* Adjust image gallery for smaller extracted images */
.image-gallery {
  margin-top: 1rem;
}

.image-card {
  position: relative;
  border-radius: 0.5rem;
  overflow: hidden;
  cursor: pointer;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  transition: all 0.3s ease;
}

.image-card img {
  width: 100%;
  height: 120px;
  object-fit: cover;
  display: block;
}
</style> 