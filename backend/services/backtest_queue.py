"""
回测后台任务队列服务

功能：
- 提交回测到后台队列
- 异步执行回测（不阻塞响应）
- 查询回测状态
- 获取回测结果

生产环境建议：
- 使用 Redis/Celery 替代内存队列
- 添加任务持久化
- 实现任务优先级队列
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class BacktestQueue:
    """
    回测任务内存队列

    注意：这是简单的内存实现，适合单实例部署
    生产环境建议使用：
    - Redis Queue + RQ Worker
    - Celery + Redis/RabbitMQ
    """

    def __init__(self):
        self.jobs: Dict[str, Dict] = {}
        self.job_counter = 0
        self.max_jobs = 100  # 最大并发任务数

    async def submit_backtest(
        self,
        request_data: dict,
        db_session
    ) -> str:
        """
        提交回测到后台队列

        Args:
            request_data: 回测请求数据
            db_session: 数据库会话

        Returns:
            job_id: 任务 ID
        """
        job_id = f"backtest_{self.job_counter}_{int(datetime.now().timestamp())}"
        self.job_counter += 1

        # 初始化任务状态
        self.jobs[job_id] = {
            "status": "pending",
            "progress": 0,
            "result": None,
            "error": None,
            "created_at": datetime.now().isoformat(),
            "started_at": None,
            "completed_at": None,
            "request": request_data
        }

        # 检查队列容量
        if len(self.jobs) > self.max_jobs:
            # 清理已完成的旧任务
            self._cleanup_old_jobs()

        # 后台运行回测
        asyncio.create_task(self._run_backtest_async(job_id, request_data, db_session))

        logger.info(f"回测任务已提交: {job_id}")
        return job_id

    async def _run_backtest_async(
        self,
        job_id: str,
        request_data: dict,
        db_session
    ):
        """
        后台运行回测

        Args:
            job_id: 任务 ID
            request_data: 回测请求数据
            db_session: 数据库会话
        """
        try:
            # 更新状态为运行中
            self.jobs[job_id]["status"] = "running"
            self.jobs[job_id]["progress"] = 10
            self.jobs[job_id]["started_at"] = datetime.now().isoformat()

            logger.info(f"开始执行回测任务: {job_id}")

            # 导入在这里执行以避免循环导入
            from backtest_engine import run_backtest
            from schemas import BacktestRequest

            # 构建请求对象
            request = BacktestRequest(**request_data)

            # 执行回测（这可能需要几分钟）
            result = await run_backtest(request, db_session)

            # 保存结果
            self.jobs[job_id]["status"] = "completed"
            self.jobs[job_id]["progress"] = 100
            self.jobs[job_id]["result"] = result.model_dump() if hasattr(result, 'model_dump') else result
            self.jobs[job_id]["completed_at"] = datetime.now().isoformat()

            logger.info(f"回测任务完成: {job_id}")

        except Exception as e:
            # 标记任务失败
            self.jobs[job_id]["status"] = "failed"
            self.jobs[job_id]["error"] = str(e)
            self.jobs[job_id]["completed_at"] = datetime.now().isoformat()

            logger.error(f"回测任务失败: {job_id}, 错误: {str(e)}")

    def get_job_status(self, job_id: str) -> Dict:
        """
        获取回测任务状态

        Args:
            job_id: 任务 ID

        Returns:
            任务状态信息
        """
        return self.jobs.get(job_id, {
            "error": "任务不存在"
        })

    def get_all_jobs(self) -> List[Dict]:
        """获取所有任务"""
        return list(self.jobs.values())

    def get_active_jobs(self) -> List[Dict]:
        """获取活跃任务（pending + running）"""
        return [
            job for job in self.jobs.values()
            if job["status"] in ["pending", "running"]
        ]

    def _cleanup_old_jobs(self):
        """清理已完成的旧任务（保留最近 50 个）"""
        completed_jobs = [
            (job_id, job)
            for job_id, job in self.jobs.items()
            if job["status"] in ["completed", "failed"]
        ]

        # 按完成时间排序
        completed_jobs.sort(
            key=lambda x: x[1].get("completed_at", ""),
            reverse=True
        )

        # 保留最近的 50 个，删除其余的
        if len(completed_jobs) > 50:
            for job_id, _ in completed_jobs[50:]:
                del self.jobs[job_id]
                logger.info(f"清理旧任务: {job_id}")

    def clear_completed_jobs(self):
        """清除所有已完成的任务"""
        jobs_to_delete = [
            job_id
            for job_id, job in self.jobs.items()
            if job["status"] in ["completed", "failed"]
        ]

        for job_id in jobs_to_delete:
            del self.jobs[job_id]

        logger.info(f"清除了 {len(jobs_to_delete)} 个已完成的任务")


# 全局队列实例
backtest_queue = BacktestQueue()
