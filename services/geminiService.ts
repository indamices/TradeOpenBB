import { GoogleGenAI, Type } from "@google/genai";
import { StrategyGenerationResponse } from '../types';

// Initialize Gemini Client
const apiKey = process.env.API_KEY || 'mock-key'; // Fallback for demo if env not set
const ai = new GoogleGenAI({ apiKey });

export const generateStrategyCode = async (userPrompt: string): Promise<StrategyGenerationResponse> => {
  try {
    // Using gemini-3-pro-preview for complex coding tasks
    const modelId = "gemini-3-pro-preview";

    const systemInstruction = `
      You are an expert Quantitative Analyst and Python developer specialized in algorithmic trading.
      Your task is to generate Python strategy code compatible with the 'SmartQuant' backtesting engine (Pandas-based).
      
      The strategy function signature should be:
      def strategy_logic(df: pd.DataFrame) -> pd.Series:
      
      The input 'df' contains columns: ['Open', 'High', 'Low', 'Close', 'Volume'].
      The output should be a Series of signals: 1 (Buy), -1 (Sell), 0 (Hold).
      
      Ensure you import necessary libraries (pandas, numpy, talib if needed).
      Prioritize vectorized operations over loops for performance.
    `;

    const response = await ai.models.generateContent({
      model: modelId,
      contents: userPrompt,
      config: {
        systemInstruction: systemInstruction,
        responseMimeType: "application/json",
        responseSchema: {
          type: Type.OBJECT,
          properties: {
            code: {
              type: Type.STRING,
              description: "The executable Python code for the strategy.",
            },
            explanation: {
              type: Type.STRING,
              description: "A brief explanation of the strategy logic.",
            },
          },
          required: ["code", "explanation"],
        },
      },
    });

    const resultText = response.text;
    if (!resultText) {
      throw new Error("No content generated");
    }

    return JSON.parse(resultText) as StrategyGenerationResponse;

  } catch (error) {
    console.error("Gemini API Error:", error);
    // Fallback Mock response if API key is invalid or fails (common in demo environments)
    return {
      code: `import pandas as pd\nimport numpy as np\n\ndef strategy_logic(df):\n    # Mock Strategy generated due to API Error\n    df['SMA_20'] = df['Close'].rolling(window=20).mean()\n    df['Signal'] = 0\n    df.loc[df['Close'] > df['SMA_20'], 'Signal'] = 1\n    df.loc[df['Close'] < df['SMA_20'], 'Signal'] = -1\n    return df['Signal']`,
      explanation: "Error connecting to AI. Returned a default SMA Crossover strategy template."
    };
  }
};

export const predictTrend = async (symbol: string, recentDataStr: string): Promise<string> => {
    try {
        const modelId = "gemini-3-flash-preview"; // Faster model for quick analysis
        const response = await ai.models.generateContent({
            model: modelId,
            contents: `Analyze the following recent price data for ${symbol} and predict the short-term trend (Bullish/Bearish/Neutral) with a confidence score (0-100). Data: ${recentDataStr}`,
            config: {
                responseMimeType: "application/json",
                responseSchema: {
                    type: Type.OBJECT,
                    properties: {
                        trend: { type: Type.STRING },
                        confidence: { type: Type.NUMBER },
                        reasoning: { type: Type.STRING }
                    }
                }
            }
        });
        return response.text || "{}";
    } catch (e) {
        console.error(e);
        return JSON.stringify({ trend: "Neutral", confidence: 50, reasoning: "AI Service Unavailable" });
    }
}
