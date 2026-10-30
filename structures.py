"""
论文的组织架构
"""
STRUCTURES = {
    "IMRD":{
        "name":"IMRD结构",
        "description":"科学论文常用的结构：Introduction（引言）、Methods（方法）、Results（结果）、Discussion（讨论）",
        "sections":[
            {"key": "Introduction", "name": "引言", "description": "介绍研究背景、问题和目的"},
            {"key": "Methods", "name": "方法", "description": "描述实验设计、数据收集和分析方法"},
            {"key": "Results", "name": "结果", "description": "呈现实验结果和数据"},
            {"key": "Discussion", "name": "讨论", "description": "解释结果、讨论意义并得出最终结论"}
        ]
    },
    "Lab_Report":{
        "name":"实验报告结构",
        "description":"实验报告常用的结构：目的、原理、步骤、数据、分析",
        "sections":[
            {"key": "Objective", "name": "目的", "description": "说明实验的目的和研究问题"},
            {"key": "Principle", "name": "原理", "description": "解释实验所依据的科学原理"},
            {"key": "Procedure", "name": "步骤", "description": "详细描述实验的操作步骤"},
            {"key": "Data", "name": "数据", "description": "记录实验过程中收集的数据"},
            {"key": "Analysis", "name": "分析", "description": "对数据进行分析并得出结论"}
        ]
    },
    "Customized":{
        "name":"自定义结构",
        "description":"用户自定义的论文结构"
    }
}