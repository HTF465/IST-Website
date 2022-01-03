class Messages extends React.Component {
    constructor(props) {
        super(props)
        this.error = this.error.bind(this)
        this.update = this.update.bind(this)
        this.refresh = this.refresh.bind(this)
        this.state = {}
    }

    error(message, jqXHR) {
        this.props.onError(message, jqXHR)
    }

    update() {
        this.setState({messages: undefined})
        this.request = $.ajax({
            url: '/api/messages',
            type: 'GET',
            dataType: 'json',
            error: (jqXHR) => this.error("Failed to load messages", jqXHR),
            success: (data) => this.setState({messages: data}),
        })
    }

    refresh(e) {
        this.componentWillUnmount()
        this.componentDidMount()
    }

    componentDidMount() {
        this.update()
        this.interval = setInterval(this.update, 3 * 60 * 1000)
    }

    componentWillUnmount() {
        clearInterval(this.interval)
        if (this.request !== undefined) {
            this.request.abort()
        }
    }

    render() {
        if (this.state.messages !== undefined) {
            return (
                <div>
                    <h2>Messages</h2>
                    <ul id="messages" className="list-group">
                        {this.state.messages.map((item) => <li className="list-group-item row" key={item} dangerouslySetInnerHTML={{__html: item}} />)}
                    </ul>
                </div>
            )
        }
        else {
            return <div className="alert alert-warning">Loading...</div>
        }
    }
}

class Courses extends React.Component {
    constructor(props) {
        super(props)
        this.error = this.error.bind(this)
        this.update = this.update.bind(this)
        this.refresh = this.refresh.bind(this)
        this.state = {}
    }

    error(message, jqXHR) {
        this.props.onError(message, jqXHR)
    }

    update() {
        this.setState({courses: undefined})
        this.request = $.ajax({
            url: '/api/courses',
            type: 'GET',
            dataType: 'json',
            error: (jqXHR) => this.error("Failed to load courses", jqXHR),
            success: (data) => this.setState({courses: data}),
        })
    }

    refresh(e) {
        this.componentWillUnmount()
        this.componentDidMount()
    }

    componentDidMount() {
        this.update()
        this.interval = setInterval(this.update, 3 * 60 * 1000)
    }

    componentWillUnmount() {
        clearInterval(this.interval)
        if (this.request !== undefined) {
            this.request.abort()
        }
    }

    render() {
        if (this.state.courses !== undefined) {
            return (
                <div>
                    <h2>Course Availability</h2>
                    <div className="table-responsive">
                        <table id="course-availability" className="table-striped table-bordered table-condensed">
                            <thead>
                                <tr>
                                    <th>Course</th>
                                    <th># Tickets</th>
                                    <th># Tutors</th>
                                </tr>
                            </thead>
                            <tbody>
                                {this.state.courses.map((item) => (
                                    <tr key={item.name}>
                                        <td>{item.name}</td>
                                        <td className="centered">{item.current_tickets}</td>
                                        <td className="centered">{item.current_tutors}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )
        }
        else {
            return <div className="alert alert-warning">Loading...</div>
        }
    }
}

class Status extends React.Component {
    constructor(props) {
        super(props)
        this.error = this.error.bind(this)
        this.refresh = this.refresh.bind(this)
        this.state = {}
    }

    error(message, jqXHR) {
        this.setState({'error': message})
    }

    componentDidCatch(error, info) {
        this.error("Unknown error")
    }

    refresh(e) {
        this.messages.refresh(e)
        this.courses.refresh(e)
    }

    render() {
        let body
        if (this.state.error === undefined) {
            body = (
                <div className="clearfix">
                    <Messages onError={this.error} ref={(t) => this.messages = t} />
                    <Courses onError={this.error} ref={(t) => this.courses = t}/>
                    <br />
                    <button className="btn btn-info pull-right" onClick={this.refresh}>Refresh</button>
                </div>
            )
        }
        else {
            body = <div className="alert alert-danger">{this.state.error}</div>
        }
        return (
            <div className="container">
                <h1>Welcome to the Computer Science Learning Center</h1>
                {body}
            </div>
        )
    }
}

ReactDOM.render(
    <Status />,
    document.getElementById("root")
)
