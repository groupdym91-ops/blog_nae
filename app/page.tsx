"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";

interface Account {
  id: string;
  naverId: string;
  naverPw: string;
}

interface Message {
  id: string;
  content: string;
}

interface LogEntry {
  id: string;
  timestamp: string;
  type: "info" | "success" | "error" | "warning";
  message: string;
}

export default function Home() {
  // 계정 관리
  const [accounts, setAccounts] = useState<Account[]>([
    { id: "1", naverId: "", naverPw: "" },
  ]);
  const [selectedAccountId, setSelectedAccountId] = useState<string>("1");

  // 메시지 관리
  const [messages, setMessages] = useState<Message[]>([
    { id: "1", content: "안녕하세요! 서로이웃 신청드립니다." },
  ]);
  const [selectedMessageId, setSelectedMessageId] = useState<string>("1");

  // 키워드
  const [keyword, setKeyword] = useState<string>("");

  // 로그
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const logRef = useRef<HTMLDivElement>(null);

  // 실행 상태
  const [isRunning, setIsRunning] = useState(false);

  // 로그 자동 스크롤
  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [logs]);

  // 로그 추가 함수
  const addLog = (type: LogEntry["type"], message: string) => {
    const now = new Date();
    const timestamp = now.toLocaleTimeString("ko-KR", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
    setLogs((prev) => [
      ...prev,
      { id: Date.now().toString(), timestamp, type, message },
    ]);
  };

  // 계정 추가
  const addAccount = () => {
    const newId = Date.now().toString();
    setAccounts((prev) => [...prev, { id: newId, naverId: "", naverPw: "" }]);
    setSelectedAccountId(newId);
  };

  // 계정 삭제
  const removeAccount = (id: string) => {
    if (accounts.length === 1) return;
    setAccounts((prev) => prev.filter((acc) => acc.id !== id));
    if (selectedAccountId === id) {
      setSelectedAccountId(accounts[0].id === id ? accounts[1]?.id : accounts[0].id);
    }
  };

  // 계정 업데이트
  const updateAccount = (id: string, field: "naverId" | "naverPw", value: string) => {
    setAccounts((prev) =>
      prev.map((acc) => (acc.id === id ? { ...acc, [field]: value } : acc))
    );
  };

  // 메시지 추가
  const addMessage = () => {
    const newId = Date.now().toString();
    setMessages((prev) => [...prev, { id: newId, content: "" }]);
    setSelectedMessageId(newId);
  };

  // 메시지 삭제
  const removeMessage = (id: string) => {
    if (messages.length === 1) return;
    setMessages((prev) => prev.filter((msg) => msg.id !== id));
    if (selectedMessageId === id) {
      setSelectedMessageId(messages[0].id === id ? messages[1]?.id : messages[0].id);
    }
  };

  // 메시지 업데이트
  const updateMessage = (id: string, content: string) => {
    setMessages((prev) =>
      prev.map((msg) => (msg.id === id ? { ...msg, content } : msg))
    );
  };

  // 실행
  const handleStart = async () => {
    const selectedAccount = accounts.find((acc) => acc.id === selectedAccountId);
    const selectedMessage = messages.find((msg) => msg.id === selectedMessageId);

    if (!selectedAccount?.naverId || !selectedAccount?.naverPw) {
      addLog("error", "네이버 아이디와 비밀번호를 입력해주세요.");
      return;
    }

    if (!keyword.trim()) {
      addLog("error", "검색 키워드를 입력해주세요.");
      return;
    }

    if (!selectedMessage?.content) {
      addLog("error", "서로이웃 신청 메시지를 입력해주세요.");
      return;
    }

    setIsRunning(true);
    setLogs([]);

    addLog("info", "서로이웃 자동 신청을 시작합니다...");
    addLog("info", `계정: ${selectedAccount.naverId}`);
    addLog("info", `키워드: ${keyword}`);
    addLog("info", `메시지: ${selectedMessage.content}`);

    try {
      const response = await fetch("/api/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          naverId: selectedAccount.naverId,
          naverPw: selectedAccount.naverPw,
          keyword: keyword,
          message: selectedMessage.content,
        }),
      });

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const text = decoder.decode(value);
          const lines = text.split("\n").filter((line) => line.trim());

          for (const line of lines) {
            try {
              const data = JSON.parse(line);
              addLog(data.type || "info", data.message);
            } catch {
              if (line.trim()) {
                addLog("info", line);
              }
            }
          }
        }
      }

      addLog("success", "작업이 완료되었습니다.");
    } catch (error) {
      addLog("error", `오류 발생: ${error}`);
    } finally {
      setIsRunning(false);
    }
  };

  // 중지
  const handleStop = async () => {
    try {
      await fetch("/api/stop", { method: "POST" });
      addLog("warning", "작업이 중지되었습니다.");
    } catch (error) {
      addLog("error", `중지 오류: ${error}`);
    }
    setIsRunning(false);
  };

  // 로그 색상
  const getLogColor = (type: LogEntry["type"]) => {
    switch (type) {
      case "success":
        return "text-green-400";
      case "error":
        return "text-red-400";
      case "warning":
        return "text-yellow-400";
      default:
        return "text-slate-300";
    }
  };

  return (
    <main className="min-h-screen p-6 bg-[#0f172a]">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-6xl mx-auto"
      >
        {/* 헤더 */}
        <motion.header
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="text-center mb-8"
        >
          <h1 className="text-3xl font-bold text-white mb-2">
            네이버 서로이웃 자동 신청
          </h1>
          <p className="text-slate-400">
            키워드로 검색된 블로그에 자동으로 서로이웃을 신청합니다
          </p>
        </motion.header>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 왼쪽 패널 */}
          <div className="space-y-6">
            {/* 계정 관리 */}
            <motion.section
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 }}
              className="bg-[#1e293b] rounded-xl p-5 border border-[#334155]"
            >
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                  <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
                  네이버 계정
                </h2>
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={addAccount}
                  className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg"
                >
                  + 계정 추가
                </motion.button>
              </div>

              {/* 계정 탭 */}
              <div className="flex gap-2 mb-4 flex-wrap">
                {accounts.map((account, index) => (
                  <motion.button
                    key={account.id}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => setSelectedAccountId(account.id)}
                    className={`px-3 py-1.5 rounded-lg text-sm flex items-center gap-2 ${
                      selectedAccountId === account.id
                        ? "bg-blue-600 text-white"
                        : "bg-[#334155] text-slate-300 hover:bg-[#475569]"
                    }`}
                  >
                    계정 {index + 1}
                    {accounts.length > 1 && (
                      <span
                        onClick={(e) => {
                          e.stopPropagation();
                          removeAccount(account.id);
                        }}
                        className="hover:text-red-400 cursor-pointer"
                      >
                        x
                      </span>
                    )}
                  </motion.button>
                ))}
              </div>

              {/* 계정 입력 */}
              <AnimatePresence mode="wait">
                {accounts
                  .filter((acc) => acc.id === selectedAccountId)
                  .map((account) => (
                    <motion.div
                      key={account.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      className="space-y-3"
                    >
                      <div>
                        <label className="block text-sm text-slate-400 mb-1.5">
                          아이디
                        </label>
                        <input
                          type="text"
                          value={account.naverId}
                          onChange={(e) =>
                            updateAccount(account.id, "naverId", e.target.value)
                          }
                          placeholder="네이버 아이디"
                          className="w-full px-4 py-2.5 bg-[#0f172a] border border-[#334155] rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
                        />
                      </div>
                      <div>
                        <label className="block text-sm text-slate-400 mb-1.5">
                          비밀번호
                        </label>
                        <input
                          type="password"
                          value={account.naverPw}
                          onChange={(e) =>
                            updateAccount(account.id, "naverPw", e.target.value)
                          }
                          placeholder="비밀번호"
                          className="w-full px-4 py-2.5 bg-[#0f172a] border border-[#334155] rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
                        />
                      </div>
                    </motion.div>
                  ))}
              </AnimatePresence>
            </motion.section>

            {/* 메시지 관리 */}
            <motion.section
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3 }}
              className="bg-[#1e293b] rounded-xl p-5 border border-[#334155]"
            >
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                  <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                  서로이웃 메시지
                </h2>
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={addMessage}
                  className="px-3 py-1.5 bg-green-600 hover:bg-green-700 text-white text-sm rounded-lg"
                >
                  + 메시지 추가
                </motion.button>
              </div>

              {/* 메시지 탭 */}
              <div className="flex gap-2 mb-4 flex-wrap">
                {messages.map((msg, index) => (
                  <motion.button
                    key={msg.id}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => setSelectedMessageId(msg.id)}
                    className={`px-3 py-1.5 rounded-lg text-sm flex items-center gap-2 ${
                      selectedMessageId === msg.id
                        ? "bg-green-600 text-white"
                        : "bg-[#334155] text-slate-300 hover:bg-[#475569]"
                    }`}
                  >
                    메시지 {index + 1}
                    {messages.length > 1 && (
                      <span
                        onClick={(e) => {
                          e.stopPropagation();
                          removeMessage(msg.id);
                        }}
                        className="hover:text-red-400 cursor-pointer"
                      >
                        x
                      </span>
                    )}
                  </motion.button>
                ))}
              </div>

              {/* 메시지 입력 */}
              <AnimatePresence mode="wait">
                {messages
                  .filter((msg) => msg.id === selectedMessageId)
                  .map((msg) => (
                    <motion.div
                      key={msg.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                    >
                      <textarea
                        value={msg.content}
                        onChange={(e) => updateMessage(msg.id, e.target.value)}
                        placeholder="서로이웃 신청 메시지를 입력하세요"
                        rows={3}
                        className="w-full px-4 py-2.5 bg-[#0f172a] border border-[#334155] rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-green-500 transition-colors resize-none"
                      />
                    </motion.div>
                  ))}
              </AnimatePresence>
            </motion.section>

            {/* 키워드 입력 */}
            <motion.section
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.4 }}
              className="bg-[#1e293b] rounded-xl p-5 border border-[#334155]"
            >
              <h2 className="text-lg font-semibold text-white flex items-center gap-2 mb-4">
                <span className="w-2 h-2 bg-purple-500 rounded-full"></span>
                검색 키워드
              </h2>
              <input
                type="text"
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                placeholder="블로그 검색 키워드를 입력하세요"
                className="w-full px-4 py-2.5 bg-[#0f172a] border border-[#334155] rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-purple-500 transition-colors"
              />
            </motion.section>

            {/* 실행 버튼 */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
              className="flex gap-3"
            >
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={handleStart}
                disabled={isRunning}
                className={`flex-1 py-3 rounded-xl font-semibold text-white ${
                  isRunning
                    ? "bg-slate-600 cursor-not-allowed"
                    : "bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
                }`}
              >
                {isRunning ? (
                  <span className="flex items-center justify-center gap-2">
                    <motion.span
                      animate={{ rotate: 360 }}
                      transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                      className="w-5 h-5 border-2 border-white border-t-transparent rounded-full"
                    />
                    실행 중...
                  </span>
                ) : (
                  "서로이웃 신청 시작"
                )}
              </motion.button>
              {isRunning && (
                <motion.button
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={handleStop}
                  className="px-6 py-3 bg-red-600 hover:bg-red-700 rounded-xl font-semibold text-white"
                >
                  중지
                </motion.button>
              )}
            </motion.div>
          </div>

          {/* 오른쪽 패널 - 로그 */}
          <motion.section
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-[#1e293b] rounded-xl p-5 border border-[#334155] flex flex-col h-[calc(100vh-12rem)]"
          >
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                <span className="w-2 h-2 bg-yellow-500 rounded-full"></span>
                실시간 로그
              </h2>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setLogs([])}
                className="px-3 py-1.5 bg-[#334155] hover:bg-[#475569] text-slate-300 text-sm rounded-lg"
              >
                로그 지우기
              </motion.button>
            </div>

            <div
              ref={logRef}
              className="flex-1 bg-[#0f172a] rounded-lg p-4 overflow-y-auto font-mono text-sm"
            >
              {logs.length === 0 ? (
                <p className="text-slate-500 text-center mt-10">
                  로그가 여기에 표시됩니다
                </p>
              ) : (
                <AnimatePresence>
                  {logs.map((log) => (
                    <motion.div
                      key={log.id}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      className={`mb-1.5 ${getLogColor(log.type)}`}
                    >
                      <span className="text-slate-500">[{log.timestamp}]</span>{" "}
                      {log.message}
                    </motion.div>
                  ))}
                </AnimatePresence>
              )}
            </div>
          </motion.section>
        </div>
      </motion.div>
    </main>
  );
}
