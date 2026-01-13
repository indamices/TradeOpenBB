import { StrategyGenerationRequest, StrategyGenerationResponse } from '../types';
import { tradingService } from './tradingService';

export const generateStrategyCode = async (
  prompt: string,
  modelId?: number
): Promise<StrategyGenerationResponse> => {
  const request: StrategyGenerationRequest = {
    prompt,
    model_id: modelId
  };
  
  return await tradingService.generateStrategy(request);
};
