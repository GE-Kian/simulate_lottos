from app import app

def main():
    """
    主函数，用于启动Flask应用
    """
    # 设置Flask应用配置
    app.config.update(
        # 启用调试模式
        DEBUG=True,
        # 设置主机，允许外部访问
        HOST='0.0.0.0',
        # 设置端口
        PORT=5000,
        # 设置JSON自动排序
        JSON_SORT_KEYS=False,
        # 设置JSON缩进
        JSONIFY_PRETTYPRINT_REGULAR=True
    )
    
    # 启动应用
    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG']
    )

if __name__ == '__main__':
    main()