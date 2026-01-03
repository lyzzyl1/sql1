import streamlit as st
import pandas as pd
import plotly.express as px
import json
from datetime import datetime
import os
from supabase import create_client, Client

st.set_page_config(page_title="跑步模拟系统", layout="wide")

# ========== 数据库连接部分 ==========
@st.cache_resource
def init_connection() -> Client:
    """创建Supabase客户端"""
    # 🔥 修改这里的值为您的实际值！ 🔥
    url = "https://fmritvcqvyhdxdjzxykl.supabase.co"  # 从图片获取的项目URL
    key = "sb_publishable_U9V_dTYIVHT6sa15IzOL1A_ql-_D7AW"  # 需要在Supabase设置->API中找到
    

    
    if not url or not key:
        st.error("请配置Supabase连接信息！")
        return None
    
    try:
        supabase = create_client(url, key)
        st.success("✅ 数据库连接成功！")
        return supabase
    except Exception as e:
        st.error(f"❌ 数据库连接失败: {e}")
        return None

def save_simulation_data_to_supabase(user_name, answer, history):
    """保存数据到Supabase"""
    supabase = init_connection()
    if not supabase:
        return False
    
    try:
        data = {
            "user_name": user_name,
            "answer": answer,
            "history_data": json.dumps(str(history), ensure_ascii=False)
        }
        
        response = supabase.table("simulation_records").insert(data).execute()
        
        if response.data:
            return True
        else:
            st.error(f"保存失败: {response.error}")
            return False
    except Exception as e:
        st.error(f"保存到数据库时出错: {e}")
        return False

def fetch_all_data_from_supabase():
    """从Supabase获取所有记录"""
    supabase = init_connection()
    if not supabase:
        return pd.DataFrame()
    
    try:
        response = supabase.table("simulation_records").select("*").order("submit_time", desc=True).execute()
        
        data = []
        for record in response.data:
            data.append({
                "编号": record.get("id", ""),
                "姓名": record.get("user_name", ""),
                "提交时间": record.get("submit_time", ""),
                "答案": record.get("answer", ""),
                "历史数据": json.loads(record.get("history_data", "[]"))
            })
        
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"查询数据失败: {e}")
        return pd.DataFrame()

# ========== 界面部分 ==========
# 左侧栏 - 输入控件（完全不变）
with st.sidebar:
    st.header("🏃 跑步模拟设置") #标题
    #交互模块（滑动条、下拉选择、按钮）
    temp = st.slider("空气温度 (°C)", 20, 40, 25, step=5)
    humidity = st.slider("空气湿度 (%)", 10, 90, 40, step=20)
    water = st.selectbox("是否喝水", ["是", "否"])
    run_button = st.button("开始模拟", type="primary")

# 主界面（完全不变）
col1, col2=st.columns([1,2])  #两列宽度比

with col1:

    # 添加用户名输入
    user_name = st.text_input("👤 请输入您的姓名", "")
    if user_name:
        st.session_state.user_name = user_name

    st.header("📝 问题描述")
    st.write("在炎热干燥天气下（气温40°C，湿度20%）跑步1小时不喝水，会遇到什么健康危险？")
    
    answer = st.selectbox(
        "选择健康危险:",
        ["无危险", "脱水 (Dehydration)", "中暑 (Heat Stroke)", "热衰竭 (Heat Exhaustion)", "低温症 (Hypothermia)"]
    ) #下拉选择框
    
    if answer:#绿色成功提示框
        st.success(f"您选择了: **{answer}**")


with col2:
    if run_button:#如果按了该按钮
        st.header("📊 模拟结果")
        #开始模拟计算
        # 简化计算逻辑
        sweat = round(0.5 + (temp - 20) * 0.1, 1)
        water_loss = round(sweat * 0.7 + (-0.3 if water == "是" else 0), 1)
        body_temp = round(37 + (temp - 25) * 0.1 + (water_loss * 0.05 if water == "否" else 0), 1)
                
        # 建立图表
        data = pd.DataFrame({
            "指标": ["温度", "湿度", "出汗量", "水分流失", "体温"],
            "值": [temp, humidity, sweat, water_loss, body_temp]
        })
        
                        
        # 历史记录（原代码不变，只显示最近5次）
        if "history" not in st.session_state:
            st.session_state.history = []
        
        st.session_state.history.append({
            "温度": temp, "湿度": humidity, "喝水": water,
            "出汗量": sweat, "水分流失": water_loss, "体温": body_temp
        })
        
        if st.session_state.history:#如果非空
            st.subheader("📈 数据记录")
            df = pd.DataFrame(st.session_state.history[-5:])  # 显示最近5次
            st.dataframe(df)



st.divider()
st.header("💾 数据提交") 

col_submit = st.columns([1])[0]
with col_submit:
    submit_button = st.button("✅ 提交答案",  type="primary",)
    # 处理提交按钮点击
if submit_button:
    if save_simulation_data_to_supabase(user_name,answer,st.session_state.history):
        st.success("✅ 数据已成功保存到后台！")


