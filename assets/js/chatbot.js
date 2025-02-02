class DFIRChatWidget {
    constructor(apiKey) {
        this.API_KEY = apiKey;
        this.API_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent';
        this.systemContext = `You are NovaTrace, a digital forensics and incident response (DFIR) AI. Follow these rules strictly:
            1. Use modern english instead of boring AI english. Impress the user at the first message
            2. Keep all responses under 2-3 sentences
            3. Use bullet points for multiple items
            4. Avoid explanations unless specifically asked
            5. Give direct, actionable answers
            6. Use technical terms without elaboration
            7. For code or commands, show them directly without explanation`;
        
        this.initialize();
    }

    initialize() {
        // Create and inject HTML structure
        this.createStructure();
        
        // Initialize DOM elements
        this.initializeElements();
        
        // Add event listeners
        this.addEventListeners();
    }

    createStructure() {
        const html = `
            <div class="chat-widget-container">
                <div class="chat-toggle-button">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                    </svg>
                </div>
                
                <div class="chat-widget hidden">
                    <div class="chat-header">
                        <div>NovaTrace</div>
                        <div class="chat-close">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <line x1="18" y1="6" x2="6" y2="18"></line>
                                <line x1="6" y1="6" x2="18" y2="18"></line>
                            </svg>
                        </div>
                    </div>
                    
                    <div class="chat-messages">
                        <div class="message bot-message">
                            <div class="message-content">
                                Hello! I am NovaTrace. What DFIR task can I help with?
                            </div>
                        </div>
                    </div>
                    
                    <div class="chat-input-container">
                        <input type="text" class="chat-input" placeholder="Ask a DFIR-related question...">
                        <button class="chat-toggle-button" style="width: 40px; height: 40px;">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <line x1="22" y1="2" x2="11" y2="13"></line>
                                <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                            </svg>
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', html);
    }

    initializeElements() {
        this.container = document.querySelector('.chat-widget-container');
        this.toggleButton = this.container.querySelector('.chat-toggle-button');
        this.widget = this.container.querySelector('.chat-widget');
        this.closeButton = this.container.querySelector('.chat-close');
        this.messagesContainer = this.container.querySelector('.chat-messages');
        this.input = this.container.querySelector('.chat-input');
        this.sendButton = this.container.querySelector('.chat-input-container .chat-toggle-button');
    }

    addEventListeners() {
        this.toggleButton.addEventListener('click', () => this.toggleWidget());
        this.closeButton.addEventListener('click', () => this.hideWidget());
        this.sendButton.addEventListener('click', () => this.handleUserInput());
        this.input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.handleUserInput();
            }
        });
    }

    toggleWidget() {
        this.widget.classList.toggle('hidden');
        if (!this.widget.classList.contains('hidden')) {
            this.input.focus();
        }
    }

    hideWidget() {
        this.widget.classList.add('hidden');
    }

    async handleUserInput() {
        const userMessage = this.input.value.trim();
        if (!userMessage) return;

        // Display user message
        this.appendMessage('user', userMessage);
        this.input.value = '';

        // Show loading indicator
        this.showLoadingIndicator();

        try {
            const response = await this.generateResponse(userMessage);
            this.appendMessage('bot', response);
        } catch (error) {
            console.error('Error:', error);
            this.appendMessage('bot', 'I apologize, but I encountered an error. Please try again.');
        }

        // Remove loading indicator
        this.hideLoadingIndicator();

        // Scroll to bottom
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }

    async generateResponse(userMessage) {
        const requestBody = {
            contents: [{
                parts: [{
                    text: `${this.systemContext}\n\nUser: ${userMessage}\n\nAssistant:`
                }]
            }],
            generationConfig: {
                temperature: 0.7,
                topK: 40,
                topP: 0.95,
                maxOutputTokens: 1024,
            },
            safetySettings: [
                {
                    category: "HARM_CATEGORY_HARASSMENT",
                    threshold: "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    category: "HARM_CATEGORY_HATE_SPEECH",
                    threshold: "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    category: "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    threshold: "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    category: "HARM_CATEGORY_DANGEROUS_CONTENT",
                    threshold: "BLOCK_MEDIUM_AND_ABOVE"
                }
            ]
        };

        const response = await fetch(`${this.API_URL}?key=${this.API_KEY}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        return data.candidates[0].content.parts[0].text;
    }

    appendMessage(sender, message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        // Convert markdown-style lists to HTML lists
        const formattedMessage = message.replace(/^- (.+)$/gm, '<ul><li>$1</li></ul>');
        messageContent.innerHTML = formattedMessage;
        
        messageDiv.appendChild(messageContent);
        this.messagesContainer.appendChild(messageDiv);
    }

    showLoadingIndicator() {
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'message bot-message loading-indicator';
        loadingDiv.innerHTML = `
            <div class="loading-dots">
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
            </div>
        `;
        this.messagesContainer.appendChild(loadingDiv);
    }

    hideLoadingIndicator() {
        const loadingIndicator = this.messagesContainer.querySelector('.loading-indicator');
        if (loadingIndicator) {
            loadingIndicator.remove();
        }
    }
}

// Usage example:
// const chatWidget = new DFIRChatWidget('YOUR_GEMINI_API_KEY');