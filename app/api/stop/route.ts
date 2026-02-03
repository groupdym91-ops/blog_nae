import { NextResponse } from "next/server";
import { exec } from "child_process";

export async function POST() {
  // Windows에서 Python 프로세스 종료
  return new Promise((resolve) => {
    exec('taskkill /F /IM python.exe /T', (error) => {
      if (error) {
        resolve(NextResponse.json({ success: false, error: error.message }));
      } else {
        resolve(NextResponse.json({ success: true, message: "프로세스가 중지되었습니다." }));
      }
    });
  });
}
