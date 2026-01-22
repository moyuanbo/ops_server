/**
 * 用户管理页面专用交互逻辑
 */

$(function() {
    // 初始化页面交互
    initUserManager();

    /**
     * 初始化函数
     */
    function initUserManager() {
        initAlertAutoClose();      // 初始化提示框自动关闭
        initDropdownMenus();       // 初始化下拉菜单
        initDeleteConfirm();       // 初始化删除确认
        fixModalBug();             // 修复模态框遮罩层bug
    }

    function fixModalBug() {
        // 点击模态框关闭按钮时，强制移除所有遮罩层
        $(document).on('click', '.modal .close', function() {
            setTimeout(() => {
                $('.modal-backdrop').remove();
                $('body').removeClass('modal-open');
            }, 100);
        });
    }

    /**
     * 初始化提示框3秒后自动关闭
     */
    function initAlertAutoClose() {
        setTimeout(() => {
            $('.alert').alert('close');
        }, 3000);

        // 手动关闭按钮增强
        $('.alert .close').on('click', function() {
            $(this).parents('.alert').alert('close');
        });
    }

    /**
     * 初始化下拉菜单
     */
    function initDropdownMenus() {
        $('.user-operation-dropdown .dropdown-toggle').dropdown();
    }

    /**
     * 初始化删除确认逻辑
     */
    function initDeleteConfirm() {
        // 为删除按钮绑定事件委托
        $(document).on('click', '.delete-user-btn', function() {
            const userId = $(this).data('id');
            if (confirm('确定要删除该用户吗？此操作不可撤销！')) {
                deleteUser(userId);
            }
        });
    }

    /**
     * 发送删除用户请求
     * @param {number} userId - 用户ID
     */
    function deleteUser(userId) {
        const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

        fetch(`{{ url_for('admin.delete_user', user_id=0) }}`.replace('0', userId), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            credentials: 'same-origin'
        })
        .then(response => {
            if (response.ok) {
                return response.json().catch(() => ({ success: true }));
            }
            return response.json().catch(() => ({ success: false, msg: '删除失败' }));
        })
        .then(data => {
            if (data.success) {
                $(`#user-tr-${userId}`).remove();
                showNotification('用户删除成功', 'success');
            } else {
                showNotification(`删除失败: ${data.msg || '未知错误'}`, 'danger');
            }
        })
        .catch(error => {
            console.error('删除用户错误:', error);
            showNotification('网络错误，删除失败', 'danger');
        });
    }

    /**
     * 显示操作通知
     * @param {string} message - 通知内容
     * @param {string} type - 通知类型 (success/danger/info/warning)
     */
    function showNotification(message, type) {
        const notification = $(`
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                    <span aria-hidden="true">&times;</span>
                </button>
            </div>
        `);

        $('.container-fluid').prepend(notification);

        // 3秒后自动关闭
        setTimeout(() => {
            notification.alert('close');
        }, 3000);
    }

    // 暴露全局方法
    window.UserManager = {
        init: initUserManager,
        deleteUser: deleteUser
    };
});