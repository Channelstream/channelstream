Polymer({
    is: 'chat-avatar',
    properties: {
        email: String,
        username: String
    },
    _getAvatar: function () {
        var avatar = this.email || this.username || 'test';
        return gravatar(avatar, {
            size: 50, rating: "pg", backup: "retro", secure: true
        });
    }
});
