package dk.steffenkarlsson.sofa.networking;

import com.squareup.okhttp.Request;

/**
 * Created by steffenkarlsson on 23/12/14.
 */
@SuppressWarnings("ALL")
public abstract class HeadRequest<T> extends AbstractNoBodyRequest<T> {

    protected HeadRequest(String url) {
        super(url);
    }

    @Override
    protected Request finalizeRequest(Request.Builder builder) {
        builder = builder.head();
        return builder.build();
    }
}
