import { NextRequest } from "next/server";
import { spawn, ChildProcess } from "child_process";
import path from "path";

let currentProcess: ChildProcess | null = null;

export async function POST(request: NextRequest) {
  const body = await request.json();
  const { naverId, naverPw, keyword, message } = body;

  // 스트리밍 응답 설정
  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    start(controller) {
      const sendLog = (type: string, msg: string) => {
        const data = JSON.stringify({ type, message: msg }) + "\n";
        controller.enqueue(encoder.encode(data));
      };

      // Python 스크립트 경로
      const scriptPath = path.join(process.cwd(), "서로이웃신청_api.py");

      // 가상환경(.venv)의 파이썬을 강제로 지정
      const pythonPath = path.join(process.cwd(), ".venv", "Scripts", "python.exe");

      // Python 실행
      currentProcess = spawn(pythonPath, [
        scriptPath,
        "--naver-id", naverId,
        "--naver-pw", naverPw,
        "--keyword", keyword,
        "--message", message,
      ]);

      currentProcess.stdout?.on("data", (data: Buffer) => {
        const lines = data.toString().split("\n").filter((line: string) => line.trim());
        for (const line of lines) {
          try {
            const parsed = JSON.parse(line);
            sendLog(parsed.type || "info", parsed.message);
          } catch {
            if (line.trim()) {
              // 로그 타입 자동 감지
              let type = "info";
              if (line.includes("[성공]") || line.includes("완료")) {
                type = "success";
              } else if (line.includes("[실패]") || line.includes("오류")) {
                type = "error";
              } else if (line.includes("경고") || line.includes("중지")) {
                type = "warning";
              }
              sendLog(type, line);
            }
          }
        }
      });

      currentProcess.stderr?.on("data", (data: Buffer) => {
        const lines = data.toString().split("\n").filter((line: string) => line.trim());
        for (const line of lines) {
          if (line.trim() && !line.includes("DevTools")) {
            sendLog("error", line);
          }
        }
      });

      currentProcess.on("close", (code: number | null) => {
        if (code === 0) {
          sendLog("success", "프로그램이 정상적으로 종료되었습니다.");
        } else if (code !== null) {
          sendLog("warning", `프로그램이 종료되었습니다. (코드: ${code})`);
        }
        currentProcess = null;
        controller.close();
      });

      currentProcess.on("error", (error: Error) => {
        sendLog("error", `프로세스 오류: ${error.message}`);
        controller.close();
      });
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
      "Transfer-Encoding": "chunked",
    },
  });
}

// 현재 프로세스 가져오기 (stop에서 사용)
export { currentProcess };
