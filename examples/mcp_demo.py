"""
MCP服务使用示例
演示如何使用视频创作平台的MCP服务
"""
import asyncio
import json
from app.services.mcp.client import AdvancedVideoCreatorClient

async def demo_basic_mcp_operations():
    """演示基本的MCP操作"""
    
    print("🔌 连接到MCP服务器...")
    async with AdvancedVideoCreatorClient("http://localhost:8001/mcp") as client:
        
        # 1. 获取服务器能力
        print("\n📋 获取服务器能力...")
        try:
            # 通过REST API获取能力信息
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:8001/mcp/capabilities") as resp:
                    capabilities = await resp.json()
                    print(f"支持的资源类型: {capabilities['resources']['supported_schemes']}")
                    print(f"可用工具数量: {len(capabilities['tools']['available_tools'])}")
        except Exception as e:
            print(f"获取能力失败: {e}")
        
        # 2. 列出所有可用工具
        print("\n🛠️  列出可用工具...")
        try:
            tools = await client.list_tools()
            for tool in tools:
                print(f"- {tool['name']}: {tool['description']}")
        except Exception as e:
            print(f"列出工具失败: {e}")
        
        # 3. 创建新项目
        print("\n📁 创建新项目...")
        try:
            project_result = await client.create_project(
                name="MCP Demo Project",
                description="使用MCP服务创建的演示项目"
            )
            if project_result.get("success"):
                project_id = project_result["project_id"]
                print(f"✅ 项目创建成功: {project_id}")
                return project_id
            else:
                print(f"❌ 项目创建失败: {project_result}")
                return None
        except Exception as e:
            print(f"创建项目失败: {e}")
            return None

async def demo_video_processing_workflow():
    """演示完整的视频处理工作流"""
    
    print("\n🎬 开始视频处理工作流...")
    async with AdvancedVideoCreatorClient("http://localhost:8001/mcp") as client:
        
        # 模拟视频URL（替换为真实URL）
        video_url = "https://example.com/sample-video.mp4"
        
        try:
            # 从URL创建完整项目
            print("🚀 从URL创建视频项目...")
            project_result = await client.create_video_project_from_url(
                video_url=video_url,
                project_name="MCP Video Workflow Demo"
            )
            
            if not project_result.get("success"):
                print(f"❌ 创建项目失败: {project_result.get('error', 'Unknown error')}")
                return
            
            project_id = project_result["project_id"]
            print(f"✅ 项目创建成功: {project_id}")
            
            # 显示分析结果
            if project_result.get("analysis"):
                analysis = project_result["analysis"]
                print(f"📊 视频分析完成:")
                print(f"   - 时长: {analysis.get('duration', 'N/A')}秒")
                print(f"   - 主题: {analysis.get('topics', [])}")
                print(f"   - 情感: {analysis.get('sentiment', 'N/A')}")
            
            # 智能编辑
            print("\n🤖 执行智能编辑...")
            editing_result = await client.intelligent_video_editing(
                project_id=project_id,
                editing_instruction="创建一个30秒的精彩片段，添加动态字幕和背景音乐"
            )
            
            if editing_result.get("success"):
                print("✅ 智能编辑完成")
                suggestions = editing_result.get("suggestions", {})
                if suggestions:
                    print("编辑建议:")
                    for key, value in suggestions.items():
                        print(f"   - {key}: {value}")
                
                # 显示生成的资源
                generated_assets = editing_result.get("generated_assets", {})
                if generated_assets:
                    print("生成的资源:")
                    for asset_type, asset_data in generated_assets.items():
                        print(f"   - {asset_type}: {asset_data}")
            
        except Exception as e:
            print(f"工作流执行失败: {e}")

async def demo_media_generation():
    """演示媒体生成功能"""
    
    print("\n🎨 演示媒体生成功能...")
    async with AdvancedVideoCreatorClient("http://localhost:8001/mcp") as client:
        
        # 1. 图像生成
        print("🖼️  生成图像...")
        try:
            image_result = await client.generate_image(
                prompt="一个现代化的视频工作室，专业摄像设备，暖色调灯光",
                style="realistic",
                size="1920x1080"
            )
            
            if image_result.get("success"):
                images = image_result.get("images", [])
                print(f"✅ 成功生成 {len(images)} 张图像")
                for i, img_url in enumerate(images):
                    print(f"   - 图像 {i+1}: {img_url}")
            else:
                print(f"❌ 图像生成失败: {image_result}")
                
        except Exception as e:
            print(f"图像生成错误: {e}")
        
        # 2. 文字转语音
        print("\n🎤 文字转语音...")
        try:
            tts_result = await client.text_to_speech(
                text="欢迎来到AI驱动的视频创作平台！我们提供完整的视频处理和生成解决方案。",
                voice="default",
                language="zh-CN"
            )
            
            if tts_result.get("success"):
                audio_path = tts_result.get("audio_path")
                print(f"✅ TTS生成成功: {audio_path}")
            else:
                print(f"❌ TTS生成失败: {tts_result}")
                
        except Exception as e:
            print(f"TTS错误: {e}")

async def demo_resource_management():
    """演示资源管理功能"""
    
    print("\n📚 演示资源管理...")
    async with AdvancedVideoCreatorClient("http://localhost:8001/mcp") as client:
        
        # 1. 列出所有项目
        print("📁 列出所有项目...")
        try:
            projects = await client.list_resources("project://")
            print(f"找到 {len(projects)} 个项目:")
            for project in projects[:5]:  # 只显示前5个
                print(f"   - {project['name']} (修改时间: {project.get('modified', 'N/A')})")
        except Exception as e:
            print(f"列出项目失败: {e}")
        
        # 2. 列出媒体文件
        print("\n🎬 列出媒体文件...")
        try:
            media_types = await client.list_media_files()
            for media_type in media_types:
                print(f"   - {media_type['name']}: {media_type['type']}")
                
                # 列出具体文件
                if media_type['name'] in ['videos', 'images']:
                    files = await client.list_media_files(media_type['name'])
                    print(f"     包含 {len(files)} 个文件")
                    
        except Exception as e:
            print(f"列出媒体文件失败: {e}")

async def demo_project_analysis():
    """演示项目分析功能"""
    
    print("\n🔍 演示项目分析...")
    async with AdvancedVideoCreatorClient("http://localhost:8001/mcp") as client:
        
        # 假设我们有一个项目ID
        try:
            # 首先获取项目列表
            projects = await client.list_resources("project://")
            if not projects:
                print("没有找到项目进行分析")
                return
            
            # 选择第一个项目进行分析
            project = projects[0]
            project_id = project['name']
            
            print(f"分析项目: {project_id}")
            
            # 获取项目信息
            project_info = await client.get_project_info(project_id)
            print("项目信息:")
            print(json.dumps(project_info, indent=2, ensure_ascii=False))
            
            # 尝试获取项目分析结果
            try:
                analysis_result = await client.read_resource(f"project://{project_id}/analysis")
                print("项目分析结果:")
                print(json.dumps(analysis_result, indent=2, ensure_ascii=False))
            except:
                print("该项目还没有分析结果")
            
        except Exception as e:
            print(f"项目分析失败: {e}")

async def main():
    """主演示函数"""
    print("🎬 视频创作平台 MCP 服务演示")
    print("=" * 50)
    
    try:
        # 基本操作演示
        project_id = await demo_basic_mcp_operations()
        
        # 媒体生成演示
        await demo_media_generation()
        
        # 资源管理演示
        await demo_resource_management()
        
        # 项目分析演示
        await demo_project_analysis()
        
        # 如果有项目ID，演示完整工作流（需要真实视频URL）
        # await demo_video_processing_workflow()
        
        print("\n✅ 所有演示完成！")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  演示已中断")
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {e}")

if __name__ == "__main__":
    print("请确保MCP服务器已启动 (python -m uvicorn app.main:app --reload)")
    print("MCP服务器正在运行，开始演示...")
    # input()  # 跳过用户输入
    
    asyncio.run(main())