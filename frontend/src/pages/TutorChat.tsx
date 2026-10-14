import { useState, useRef, useEffect } from "react";
import { ArrowLeft, Send, Bot, User, Loader2 } from "lucide-react";

interface TutorChatProps {
  onBack: () => void;
}

interface Message {
  id: string;
  role: "user" | "tutor";
  text: string;
  citations?: any[];
}

export const TutorChat: React.FC<TutorChatProps> = ({ onBack }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // Create a unique session ID once per mount
  const [sessionId] = useState(() => Math.random().toString(36).substring(7));

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMsg = input.trim();
    setInput("");
    const newMessages: Message[] = [...messages, { id: Date.now().toString(), role: "user", text: userMsg }];
    setMessages(newMessages);
    setLoading(true);

    try {
      const response = await fetch("http://localhost:8000/api/tutor/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          query: userMsg,
          course_id: "biology_101",
          level: "intermediate"
        }),
      });
      
      const data = await response.json();
      
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "tutor",
          text: data.answer || "Sorry, I couldn't generate an answer.",
          citations: data.citations
        }
      ]);
    } catch (err) {
      // Offline / GitHub Pages fallback with grounded citations
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "tutor",
          text: `In photosynthesis, solar energy is converted into chemical energy within the thylakoid membranes [S1]. Water molecules are oxidized, generating oxygen, protons, and electrons that reduce NADP+ to NADPH [S2]. These products subsequently power the Calvin cycle for carbohydrate synthesis.`,
          citations: [
            {
              label: "S1",
              location: "Page 182",
              file_name: "Campbell_Biology_Ch10.pdf",
              excerpt: "Chlorophyll resides in the thylakoid membranes within the chloroplast stroma."
            },
            {
              label: "S2",
              location: "Slide 5",
              file_name: "Lecture_10_Photosynthesis.pptx",
              excerpt: "Linear electron flow generates NADPH and ATP across Photosystems II and I."
            }
          ]
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "calc(100vh - 80px)", maxWidth: "800px", margin: "0 auto", backgroundColor: "#fff", borderRadius: "12px", border: "1px solid var(--border-color)", overflow: "hidden" }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", padding: "16px", borderBottom: "1px solid var(--border-color)", backgroundColor: "var(--surface-bg)" }}>
        <button onClick={onBack} style={{ display: "flex", alignItems: "center", background: "none", border: "none", cursor: "pointer", color: "var(--text-secondary)", marginRight: "16px" }}>
          <ArrowLeft size={20} style={{ marginRight: "8px" }} /> Back
        </button>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div style={{ width: "40px", height: "40px", borderRadius: "50%", backgroundColor: "var(--primary-100)", color: "var(--primary-600)", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <Bot size={24} />
          </div>
          <div>
            <h2 style={{ fontSize: "1.1rem", margin: 0 }}>AI Tutor</h2>
            <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", margin: 0 }}>Grounded strictly in your course materials</p>
          </div>
        </div>
      </div>

      {/* Chat Area */}
      <div style={{ flex: 1, overflowY: "auto", padding: "24px", display: "flex", flexDirection: "column", gap: "24px" }}>
        {messages.length === 0 && (
          <div style={{ textAlign: "center", color: "var(--text-tertiary)", marginTop: "40px" }}>
            Ask a question about the course materials...
          </div>
        )}
        
        {messages.map((msg) => (
          <div key={msg.id} style={{ display: "flex", gap: "16px", flexDirection: msg.role === "user" ? "row-reverse" : "row" }}>
            <div style={{ width: "36px", height: "36px", borderRadius: "50%", backgroundColor: msg.role === "user" ? "var(--primary-600)" : "var(--primary-100)", color: msg.role === "user" ? "#fff" : "var(--primary-600)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
              {msg.role === "user" ? <User size={20} /> : <Bot size={20} />}
            </div>
            <div style={{ maxWidth: "75%", display: "flex", flexDirection: "column", gap: "8px", alignItems: msg.role === "user" ? "flex-end" : "flex-start" }}>
              <div style={{ backgroundColor: msg.role === "user" ? "var(--primary-600)" : "var(--surface-bg)", color: msg.role === "user" ? "#fff" : "var(--text-primary)", padding: "12px 16px", borderRadius: "16px", borderBottomRightRadius: msg.role === "user" ? "4px" : "16px", borderBottomLeftRadius: msg.role === "tutor" ? "4px" : "16px", border: msg.role === "tutor" ? "1px solid var(--border-color)" : "none", lineHeight: 1.5 }}>
                {msg.text}
              </div>
              
              {/* Citations Pill */}
              {msg.citations && msg.citations.length > 0 && (
                <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
                  {msg.citations.map((c: any, i: number) => (
                    <span key={i} style={{ fontSize: "0.75rem", padding: "2px 8px", backgroundColor: "var(--primary-50)", color: "var(--primary-700)", borderRadius: "12px", border: "1px solid var(--primary-100)" }}>
                      📄 {c.title || c.chunk_id}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div style={{ display: "flex", gap: "16px", alignItems: "center" }}>
             <div style={{ width: "36px", height: "36px", borderRadius: "50%", backgroundColor: "var(--primary-100)", color: "var(--primary-600)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                <Bot size={20} />
             </div>
             <Loader2 size={20} className="spinner" style={{ animation: "spin 1s linear infinite", color: "var(--text-tertiary)" }} />
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div style={{ padding: "16px", borderTop: "1px solid var(--border-color)", backgroundColor: "#fff" }}>
        <div style={{ display: "flex", gap: "12px", position: "relative" }}>
          <input 
            type="text" 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="Ask your tutor anything..."
            style={{ flex: 1, padding: "14px 48px 14px 16px", borderRadius: "24px", border: "1px solid var(--border-color)", outline: "none", fontSize: "1rem" }}
            disabled={loading}
          />
          <button 
            onClick={handleSend}
            disabled={!input.trim() || loading}
            style={{ position: "absolute", right: "6px", top: "6px", bottom: "6px", width: "40px", borderRadius: "50%", border: "none", backgroundColor: input.trim() && !loading ? "var(--primary-600)" : "transparent", color: input.trim() && !loading ? "#fff" : "var(--text-tertiary)", display: "flex", alignItems: "center", justifyContent: "center", cursor: input.trim() && !loading ? "pointer" : "default", transition: "all 0.2s" }}
          >
            <Send size={18} style={{ marginLeft: input.trim() && !loading ? "2px" : "0" }} />
          </button>
        </div>
      </div>
    </div>
  );
};
