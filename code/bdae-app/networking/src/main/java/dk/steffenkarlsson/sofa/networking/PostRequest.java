package dk.steffenkarlsson.sofa.networking;

import android.util.Log;

import com.squareup.okhttp.Request;
import com.squareup.okhttp.RequestBody;

/**
 * Created by steffenkarlsson on 23/12/14.
 */
@SuppressWarnings("ALL")
public abstract class PostRequest<T> extends AbstractBodyRequest<T> {

    protected PostRequest(String url) {
        super(url);
    }

    @Override
    protected Request finalizeRequest(Request.Builder builder) {
        RequestBody data = getData();
        Log.d("Networking", "Request Body: " + data.toString());
        builder.post(data);
        return builder.build();
    }

}