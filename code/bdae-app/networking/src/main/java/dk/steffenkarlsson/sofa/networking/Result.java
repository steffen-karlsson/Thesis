package dk.steffenkarlsson.sofa.networking;

/**
 * Created by steffenkarlsson on 22/12/14.
 */
@SuppressWarnings("ALL")
public class Result<T> {

    public int statusCode;
    public T response;

    public Result(int statusCode, T response) {
        this.statusCode = statusCode;
        this.response = response;
    }
}
