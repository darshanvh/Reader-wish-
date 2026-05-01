/**
 * Global AJAX Loader
 * Include this file in all your HTML templates: <script src="/static/ajax-loader.js"></script>
 * Then use: showAjaxLoader() and hideAjaxLoader()
 */

// Create global loader element on DOM load
document.addEventListener('DOMContentLoaded', function() {
  if (!document.getElementById('globalLoaderContainer')) {
    const loaderHTML = `
      <div class="global-loader-container" id="globalLoaderContainer">
        <div class="global-loader-box">
          <div class="global-loader"></div>
          <div class="global-loader-text">Loading...</div>
        </div>
      </div>
    `;
    document.body.insertAdjacentHTML('beforeend', loaderHTML);
    injectLoaderStyles();
  }
});

// Inject CSS styles for loader
function injectLoaderStyles() {
  const styleId = 'global-loader-styles';
  if (!document.getElementById(styleId)) {
    const style = document.createElement('style');
    style.id = styleId;
    style.textContent = `
      /* GLOBAL AJAX LOADER */
      .global-loader-container{
        display:none;
        position:fixed;
        top:0;
        left:0;
        width:100%;
        height:100%;
        background:rgba(0,0,0,0.6);
        justify-content:center;
        align-items:center;
        z-index:10000;
      }

      .global-loader-container.active{
        display:flex;
      }

      .global-loader-box{
        display:flex;
        flex-direction:column;
        align-items:center;
        justify-content:center;
      }

      .global-loader{
        border:8px solid #f3f3f3;
        border-top:8px solid #3498db;
        border-radius:50%;
        width:60px;
        height:60px;
        animation:globalLoaderSpin 1s linear infinite;
      }

      @keyframes globalLoaderSpin{
        0%{transform:rotate(0deg)}
        100%{transform:rotate(360deg)}
      }

      .global-loader-text{
        color:#fff;
        font-size:18px;
        margin-top:20px;
        font-weight:600;
      }
    `;
    document.head.appendChild(style);
  }
}

// Show loader
function showAjaxLoader(message = 'Loading...') {
  const container = document.getElementById('globalLoaderContainer');
  if (container) {
    const textElement = container.querySelector('.global-loader-text');
    if (textElement) {
      textElement.textContent = message;
    }
    container.classList.add('active');
  }
}

// Hide loader
function hideAjaxLoader() {
  const container = document.getElementById('globalLoaderContainer');
  if (container) {
    container.classList.remove('active');
  }
}

// Aliases for convenience
const showLoader = showAjaxLoader;
const hideLoader = hideAjaxLoader;
