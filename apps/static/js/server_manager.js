/**
 * 服务器管理通用JS逻辑
 * 包含添加/编辑服务器页面的通用交互
 */

$(function() {
    // 初始化页面
    initServerManager();

    /**
     * 初始化函数
     */
    function initServerManager() {
        initAlertClose(); // 初始化提示框关闭
        initFormValidation(); // 初始化表单验证
        initInputFormatCheck(); // 初始化输入格式校验
    }

    /**
     * 初始化提示框自动关闭（可选，增强用户体验）
     */
    function initAlertClose() {
        // 3秒后自动关闭提示框
        setTimeout(() => {
            $('.alert').alert('close');
        }, 3000);

        // 手动关闭按钮增强
        $('.alert .close').on('click', function() {
            $(this).parents('.alert').alert('close');
        });
    }

    /**
     * 初始化表单验证
     */
    function initFormValidation() {
        // 表单提交前验证
        $('form').on('submit', function(e) {
            let isValid = true;
            const requiredFields = $(this).find('[required]');

            // 遍历必填项检查
            requiredFields.each(function() {
                const $field = $(this);
                const value = $.trim($field.val());

                // 空值检查
                if (value === '') {
                    isValid = false;
                    // 高亮错误字段
                    $field.addClass('border-danger');
                    // 提示用户
                    alert($field.prev('label').text().replace(' *', '') + '不能为空');
                } else {
                    $field.removeClass('border-danger');
                }
            });

            // 验证不通过阻止提交
            if (!isValid) {
                e.preventDefault();
            }
        });

        // 输入框输入时移除错误样式
        $('[required]').on('input change', function() {
            $(this).removeClass('border-danger');
        });
    }

    /**
     * 初始化输入格式校验（IP、端口、数字等）
     */
    function initInputFormatCheck() {
        // IP地址格式校验
        $('#external_ip, #intranet_ip').on('blur', function() {
            const ip = $.trim($(this).val());
            const ipRegex = /^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$/;

            if (ip && !ipRegex.test(ip)) {
                alert('请输入正确的IP地址格式');
                $(this).addClass('border-danger').focus();
            }
        });

        // 端口号范围校验（1-65535）
        $('#ssh_port').on('blur', function() {
            const port = parseInt($(this).val());
            if (port && (port < 1 || port > 65535)) {
                alert('请输入1-65535之间的有效端口号');
                $(this).val(22).addClass('border-danger').focus();
            }
        });

        // 数字输入框校验（正整数）
        $('#cpu_info, #men_info, #hard_disk').on('blur', function() {
            const value = parseInt($(this).val());
            if (value && value < 1) {
                alert('请输入正整数');
                $(this).addClass('border-danger').focus();
            }
        });
    }

    // 暴露全局函数（可选，方便外部调用）
    window.ServerManager = {
        init: initServerManager
    };
});