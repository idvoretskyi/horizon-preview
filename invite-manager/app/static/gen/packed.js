'use strict';

class InviteManager extends React.Component {
    // Set the initial state in the constructor
    constructor(props) {
        super(props);
        this.state = {
            users: [],
            invites: {
                github: [],
                slack: []
            }
        };
    }

    componentDidMount() {
        // Fetch inital data from the server
        self = this;
        fetch('/users', { credentials: 'same-origin' }).then(output => output.json()).then(response => self.setState({ users: response.users })).catch(err => console.log('Error:', err));

        fetch('/invites/github').then(output => output.json()).then(response => {
            let invites = self.state.invites;
            invites['github'] = response.users;
            self.setState({ invites: invites });
        }).catch(err => console.log('Error:', err));

        fetch('/invites/slack').then(output => output.json()).then(response => {
            let invites = self.state.invites;
            invites['slack'] = response.users.map(u => u.email);
            self.setState({ invites: invites });
        }).catch(err => console.log('Error:', err));
    }

    render() {
        return React.createElement(
            'div',
            null,
            React.createElement(
                'header',
                null,
                React.createElement(
                    'h1',
                    null,
                    'Horizon invites'
                ),
                React.createElement(
                    'p',
                    null,
                    this.state.users.length,
                    ' total entries'
                )
            ),
            React.createElement(UserList, { users: this.state.users, invites: this.state.invites })
        );
    }
}

class UserList extends React.Component {
    render() {
        return React.createElement(
            'ul',
            { className: 'user-list' },
            this.props.users.map((user, i) => React.createElement(
                'li',
                { key: user.dateCreated },
                React.createElement(User, { key: user.dateCreated, user: user, even: i % 2 == 0, invites: this.props.invites })
            ))
        );
    }
}
class User extends React.Component {
    constructor(props) {
        super(props);
    }
    render() {
        let user = this.props.user;
        let timeago = moment(user.dateCreated, 'YYYY-MM-DD hh:mm:ss').fromNow();
        return React.createElement(
            'ul',
            { className: this.props.even ? 'user even' : 'user odd' },
            React.createElement(
                'li',
                { className: 'avatar' },
                React.createElement('img', { src: `https://github.com/${ user.github }.png?size=100`, className: 'avatar' })
            ),
            React.createElement(
                'li',
                { className: 'info' },
                React.createElement(
                    'p',
                    { className: 'github' },
                    React.createElement(
                        'a',
                        { href: `https://github.com/${ user.github }`, target: '_blank' },
                        user.github
                    )
                ),
                React.createElement(
                    'p',
                    { className: 'timeago' },
                    timeago
                ),
                React.createElement(
                    'p',
                    { className: 'email' },
                    user.email
                )
            ),
            React.createElement(
                'li',
                { className: 'invites' },
                React.createElement(
                    'ul',
                    null,
                    React.createElement(
                        'li',
                        { className: 'invite-github' },
                        React.createElement(Invite, {
                            user: user,
                            invites: this.props.invites,
                            service: 'github',
                            serviceName: 'GitHub' })
                    ),
                    React.createElement(
                        'li',
                        { className: 'invite-slack' },
                        React.createElement(Invite, {
                            user: React.addons.update(user, { $merge: { slack: user.email } }),
                            invites: this.props.invites,
                            service: 'slack',
                            serviceName: 'Slack' })
                    ),
                    React.createElement(
                        'li',
                        null,
                        React.createElement(Invite, {
                            user: user,
                            invites: this.props.invites,
                            service: 'email',
                            serviceName: 'Gmail' })
                    )
                )
            )
        );
    }
}

class Invite extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            loading: false,
            pending: false
        };
        this.requestInvite = this.requestInvite.bind(this);
        this.is_member = this.is_member.bind(this);
    }

    requestInvite(e) {
        this.setState({ loading: true });
        self = this;

        fetch(`/invites/${ this.props.service }`, {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user: this.props.user[this.props.service]
            }),
            credentials: 'same-origin'
        }).then(output => output.json()).then(response => self.setState({ loading: false, pending: true })).catch(err => console.log('Error:', err));
    }
    is_member(user) {
        let invites = this.props.invites[this.props.service];
        switch (this.props.service) {
            case 'github':
                return invites.indexOf(user.github.toLowerCase()) >= 0;
            case 'slack':
                return invites.indexOf(user.email.toLowerCase()) >= 0;
            case 'gmail':
                return false;

        }
    }
    render() {
        let user = this.props.user;
        if (this.state.pending) {
            return React.createElement(
                'p',
                null,
                'Pending'
            );
        }
        if (this.state.loading) {
            return React.createElement(
                'p',
                null,
                'Inviting...'
            );
        }
        if (this.is_member(user)) {
            switch (this.props.service) {
                case 'github':
                    return React.createElement(
                        'p',
                        null,
                        '✓ ',
                        React.createElement(
                            'a',
                            { href: `https://github.com/${ user.github }`, target: '_blank' },
                            this.props.serviceName
                        )
                    );
                case 'slack':
                    return React.createElement(
                        'p',
                        null,
                        '✓ ',
                        this.props.serviceName
                    );
            }
        }
        return React.createElement(
            'button',
            { onClick: this.requestInvite },
            'Invite on ',
            this.props.serviceName
        );
    }
}

ReactDOM.render(React.createElement(InviteManager, null), document.getElementById('container'));

