'use strict';

class InviteManager extends React.Component {
    // Set the initial state in the constructor
    constructor(props) {
        super(props)
        this.state = {
            users: [],
            invites: {
                github: [],
                slack: []
            }
        }
    }

    componentDidMount() {
        // Fetch inital data from the server
        self = this
        fetch('/users', { credentials: 'same-origin'})
            .then((output) => output.json())
            .then((response) => self.setState({users: response.users}))
            .catch((err) => console.log('Error:',err))

        fetch('/invites/github')
            .then((output) => output.json())
            .then((response) => {
                let invites = self.state.invites
                invites['github'] = response.users
                self.setState({ invites: invites})
            })
            .catch((err) => console.log('Error:',err))

        fetch('/invites/slack')
            .then((output) => output.json())
            .then((response) => {
                let invites = self.state.invites
                invites['slack'] = response.users.map((u) => u.email)
                self.setState({ invites: invites})
            })
            .catch((err) => console.log('Error:',err))
    }

    render() {
        return(
            <div>
                <header>
                    <h1>Horizon invites</h1>
                    <p>{ this.state.users.length } total entries</p>
                </header>
                <UserList users={this.state.users} invites={this.state.invites} />
            </div>
        )
    }
}

class UserList extends React.Component {
    render() {
        return(<ul className="user-list">
            {this.props.users.map(
                (user, i) => <li key={user.dateCreated}><User key={user.dateCreated} user={user} even={i%2==0} invites={this.props.invites} /></li>
            )}
        </ul>)
    }
}
class User extends React.Component {
    constructor(props) {
        super(props)
    }
    render() {
        let user = this.props.user
        let timeago = moment(user.dateCreated, 'YYYY-MM-DD hh:mm:ss').fromNow()
        return(
            <ul className={this.props.even ? 'user even' : 'user odd'}>
                <li className="avatar"><img src={`https://github.com/${user.github}.png?size=100`} className="avatar" /></li>
                <li className="info">
                    <p className="github"><a href={`https://github.com/${user.github}`} target="_blank">{user.github}</a></p>
                    <p className="timeago">{timeago}</p>
                    <p className="email">{user.email}</p>
                </li>
                <li className="invites">
                    <ul>
                        <li className="invite-github">
                            <Invite
                                user={user}
                                invites={this.props.invites}
                                service="github"
                                serviceName="GitHub" />
                        </li>
                        <li className="invite-slack">
                            <Invite
                                user={React.addons.update(user, {$merge: {slack: user.email}})}
                                invites={this.props.invites}
                                service="slack"
                                serviceName="Slack" />
                        </li>
                        <li>
                            <Invite
                                user={user}
                                invites={this.props.invites}
                                service="email"
                                serviceName="Gmail" />
                        </li>
                    </ul>
                </li>

            </ul>
        )
    }
}

class Invite extends React.Component {
    constructor(props) {
        super(props)
        this.state = {
            loading: false,
            pending: false
        }
        this.requestInvite = this.requestInvite.bind(this);
        this.is_member = this.is_member.bind(this);
    }

    requestInvite(e) {
        this.setState({loading: true})
        self = this

        fetch(`/invites/${this.props.service}`,
            {
                method: 'POST',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user: this.props.user[this.props.service]
                }),
                credentials: 'same-origin'
            })
            .then((output) => output.json())
            .then((response) => self.setState({loading: false, pending: true}))
            .catch((err) => console.log('Error:',err))
    }
    is_member(user) {
        let invites = this.props.invites[this.props.service]
        switch(this.props.service) {
            case 'github': return invites.indexOf(user.github.toLowerCase()) >= 0
            case 'slack': return invites.indexOf(user.email.toLowerCase()) >= 0
            case 'gmail': return false

        }
    }
    render() {
        let user = this.props.user
        if (this.state.pending) { return(<p>Pending</p>)}
        if (this.state.loading) { return(<p>Inviting...</p>)}
        if (this.is_member(user)) {
            switch(this.props.service) {
                case 'github': return (<p>✓ <a href={`https://github.com/${user.github}`} target="_blank">{this.props.serviceName}</a></p>)
                case 'slack': return (<p>✓ {this.props.serviceName}</p>)
            }
        }
        return(<button onClick={this.requestInvite}>Invite on {this.props.serviceName}</button>)
    }
}

ReactDOM.render(<InviteManager />,document.getElementById('container'))
