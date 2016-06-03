package dk.steffenkarlsson.sofa.networking;

import com.squareup.okhttp.RequestBody;

/**
 * Created by steffenkarlsson on 22/12/14.
 */
@SuppressWarnings("ALL")
public abstract class AbstractBodyRequest<T> extends BaseRequest<T> {

    private boolean receiveData = false;

    protected AbstractBodyRequest(String url) {
        super(url);
    }

    protected abstract RequestBody getData();

    public BaseRequest shouldReturnData() {
        this.receiveData = true;
        return this;
    }

    @Override
    public Result<T> handleResponse(int statusCode, String body) throws ParserException {
        if (receiveData) {
            T result = parseHttpResponseBody(body);
            if (result == null) {
                throw new ParserException();
            }
            else {
                return new Result<>(statusCode, result);
            }
        }
        else {
            return new Result<>(ErrorCode.NO_BODY.code, null);
        }
    }

}