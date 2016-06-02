package dk.steffenkarlsson.sofa.networking;

/**
 * Created by steffenkarlsson on 22/12/14.
 */
@SuppressWarnings("ALL")
public abstract class AbstractNoBodyRequest<T> extends BaseRequest<T> {

    protected AbstractNoBodyRequest(String url) {
        super(url);
    }

    @Override
    public Result<T> handleResponse(int statusCode, String body) throws ParserException {
        T result = parseHttpResponseBody(body);
        if (result == null) {
            throw new ParserException();
        }
        else {
            return new Result<>(statusCode, result);
        }
    }

}