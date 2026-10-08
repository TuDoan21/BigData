import streamlit as st
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dashboard"))

print("Streamlit version:", st.__version__)
print("Has st.html:", hasattr(st, "html"))

import components
print("Components file:", components.__file__)
print("Has render_html_block:", hasattr(components, "render_html_block"))
