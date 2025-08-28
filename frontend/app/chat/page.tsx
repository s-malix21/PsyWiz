"use client"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { Send, ChevronDown, ChevronUp, ExternalLink, FileText, User, Bot, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"

interface Source {
  title: string
  content: string
  metadata?: {
    authors?: string
    section?: string
    source_url?: string
    [key: string]: any
  }
}

interface Message {
  id: string
  type: 'user' | 'assistant'
  content: string
  sources?: Source[]
  timestamp: Date
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const scrollToBottom = () => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight
    }
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: input.trim(),
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput("")
    setIsLoading(true)

    try {
      const response = await fetch('http://localhost:8000/rag/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: userMessage.content,
          max_tokens: 500,
          temperature: 0.7
        })
      })

      if (!response.ok) {
        throw new Error('Failed to get response')
      }

      const data = await response.json()

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: data.answer,
        sources: data.sources,
        timestamp: new Date()
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      console.error('Error:', error)
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: "Sorry, I encountered an error while processing your question. Please try again.",
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
      inputRef.current?.focus()
    }
  }

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900">
      {/* Header */}
      <div className="border-b bg-white/80 dark:bg-slate-950/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-gradient-to-r from-blue-500 to-purple-600">
              <Bot className="h-5 w-5 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-slate-900 dark:text-slate-100">
                PsyWiz Assistant
              </h1>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                Ask questions about psychology research
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Chat Messages */}
      <ScrollArea className="flex-1 p-4" ref={scrollAreaRef}>
        <div className="container mx-auto max-w-4xl space-y-6">
          {messages.length === 0 && (
            <div className="text-center py-12">
              <div className="p-4 rounded-full bg-gradient-to-r from-blue-500 to-purple-600 w-16 h-16 mx-auto mb-4 flex items-center justify-center">
                <Bot className="h-8 w-8 text-white" />
              </div>
              <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-100 mb-2">
                Welcome to PsyWiz Assistant
              </h2>
              <p className="text-slate-600 dark:text-slate-400 max-w-md mx-auto">
                Start a conversation by asking questions about medical research. 
                I'll provide evidence-based answers with citations.
              </p>
            </div>
          )}

          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}

          {isLoading && (
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-full bg-gradient-to-r from-blue-500 to-purple-600">
                <Bot className="h-4 w-4 text-white" />
              </div>
              <Card className="flex-1 max-w-2xl">
                <CardContent className="p-4">
                  <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>Searching research papers...</span>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Input Area */}
      <div className="border-t bg-white/80 dark:bg-slate-950/80 backdrop-blur-sm p-4">
        <div className="container mx-auto max-w-4xl">
          <form onSubmit={handleSubmit} className="flex gap-2">
            <Input
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question..."
              className="flex-1 min-h-[48px] resize-none rounded-xl border-slate-300 dark:border-slate-600 focus:border-blue-500 dark:focus:border-blue-400"
              disabled={isLoading}
            />
            <Button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="h-12 w-12 rounded-xl bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 transition-all duration-200"
            >
              <Send className="h-4 w-4" />
            </Button>
          </form>
        </div>
      </div>
    </div>
  )
}

function MessageBubble({ message }: { message: Message }) {
  const isUser = message.type === 'user'

  return (
    <div className={cn("flex items-start gap-3", isUser && "flex-row-reverse")}>
      <div className={cn(
        "p-2 rounded-full",
        isUser 
          ? "bg-slate-200 dark:bg-slate-700" 
          : "bg-gradient-to-r from-blue-500 to-purple-600"
      )}>
        {isUser ? (
          <User className="h-4 w-4 text-slate-600 dark:text-slate-300" />
        ) : (
          <Bot className="h-4 w-4 text-white" />
        )}
      </div>

      <div className={cn("flex-1 max-w-2xl", isUser && "flex justify-end")}>
        <Card className={cn(
          "transition-all duration-200 hover:shadow-md",
          isUser 
            ? "bg-gradient-to-r from-blue-500 to-purple-600 text-white border-0" 
            : "bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700"
        )}>
          <CardContent className="p-4">
            <div className={cn(
              "prose prose-sm max-w-none",
              isUser ? "prose-invert" : "prose-slate dark:prose-invert"
            )}>
              <p className="whitespace-pre-wrap m-0">{message.content}</p>
            </div>

            {message.sources && message.sources.length > 0 && (
              <div className="mt-4 pt-4 border-t border-slate-200 dark:border-slate-600">
                <CitationList sources={message.sources} />
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

function CitationList({ sources }: { sources: Source[] }) {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <CollapsibleTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          className="h-auto p-0 font-normal text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100"
        >
          <div className="flex items-center gap-2">
            <FileText className="h-4 w-4" />
            <span>{sources.length} source{sources.length !== 1 ? 's' : ''}</span>
            {isOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </div>
        </Button>
      </CollapsibleTrigger>
      
      <CollapsibleContent className="space-y-2 mt-3">
        {sources.map((source, index) => (
          <Card key={index} className="bg-slate-50 dark:bg-slate-700 border-slate-200 dark:border-slate-600">
            <CardContent className="p-3">
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <Badge variant="secondary" className="text-xs">
                      {index + 1}
                    </Badge>
                    <h4 className="font-medium text-sm text-slate-900 dark:text-slate-100 truncate">
                      {source.title}
                    </h4>
                  </div>
                  
                  <p className="text-xs text-slate-600 dark:text-slate-400 mb-1">
                    {source.metadata?.authors && source.metadata.authors.trim() !== "" && <>By {source.metadata.authors}</>}
                    {source.metadata?.authors && source.metadata.authors.trim() !== "" && source.metadata?.section && source.metadata.section.trim() !== "" && " • "}
                    {source.metadata?.section && source.metadata.section.trim() !== "" && <>{source.metadata.section}</>}
                  </p>
                  
                  <p className="text-xs text-slate-700 dark:text-slate-300 line-clamp-2">
                    {source.content}
                  </p>
                </div>
                
                {source.metadata?.source_url && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 w-8 p-0 shrink-0"
                    onClick={() => window.open(source.metadata?.source_url, '_blank')}
                  >
                    <ExternalLink className="h-3 w-3" />
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </CollapsibleContent>
    </Collapsible>
  )
}