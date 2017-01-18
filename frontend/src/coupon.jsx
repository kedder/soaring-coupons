import React from "react";
import ReactDOM from "react-dom";

class CouponUI extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            coupon: props.coupon
        }

        this.handleResend = this.handleResend.bind(this);
        this.resending = false;
        this.status = '';
    }

    handleResend() {
        var url = "/api/1/coupon/" + this.state.coupon.__name + "/resend"
        var rq = new Request(url, {method: 'POST',
                                   credentials: 'same-origin'});
        fetch(rq).then((resp) => {
            this.resending = false;
            if (resp.ok) {
                this.status = " - ok"
            }
            else {
                this.status = " - klaida"
            }
            this.forceUpdate();
        })
        this.resending = true;
        this.status = '';
        this.forceUpdate();
    }

    render() {
        var resending = this.resending ? ' ...' : '';
        return (
            <div>
                <h4>Kiti vieksmai</h4>
                <button onClick={this.handleResend}>
                    Pakartoti kvietimo laišką
                    {resending} {this.status}
                </button>
            </div>
        );
    }
}

export function renderCoupon(elem, coupon) {
    // test
    ReactDOM.render(
      <CouponUI name="World" coupon={coupon} />,
      elem
    );
}
